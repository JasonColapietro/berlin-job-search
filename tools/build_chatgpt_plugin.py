from __future__ import annotations

import argparse
import io
import json
import shutil
import sys
import tempfile
import zipfile
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
PLUGIN_SOURCE = ROOT / "chatgpt" / "plugin-src"
SKILL_NAME = "berlin-job-search"
MAIN_SKILL = ROOT / "skills" / SKILL_NAME
PLUGIN_FOLDER = SKILL_NAME + "-plugin"
MAX_SKILLS = 5
MAX_FILES_PER_SKILL = 100
MAX_SKILL_MD_BYTES = 256 * 1024
MAX_SUPPORTING_FILE_BYTES = 1024 * 1024
MAX_SKILL_BYTES = 5 * 1024 * 1024
MAX_ALL_SKILLS_BYTES = 8 * 1024 * 1024
OFFLINE_SCRIPTS = ("analyze_jd.py", "ats_check.py", "render_doc.py", "tracker.py", "report.py")
OPENAI_CATEGORIES = {
    "business",
    "collaboration",
    "design",
    "developer tools",
    "education",
    "entertainment",
    "finance",
    "food",
    "lifestyle",
    "news",
    "productivity",
    "shopping",
    "travel",
}


class BuildError(ValueError):
    pass


def parse_skill_frontmatter(path: Path) -> dict[str, str]:
    content = path.read_text(encoding="utf-8")
    lines = content.splitlines()
    if not lines or lines[0].strip() != "---":
        raise BuildError("{} must begin with a YAML frontmatter block".format(path))
    end = next((index for index in range(1, len(lines)) if lines[index].strip() == "---"), None)
    if end is None:
        raise BuildError("{} has an unclosed frontmatter block".format(path))
    fields: dict[str, str] = {}
    for line in lines[1:end]:
        key, separator, value = line.partition(":")
        if separator:
            fields[key.strip()] = value.strip().strip("\"'")
    return fields


def _skill_files(skill_dir: Path) -> list[Path]:
    return sorted(
        path for path in skill_dir.rglob("*")
        if path.is_file()
        and "__pycache__" not in path.parts
        and path.suffix != ".pyc"
    )


def validate_skill(skill_dir: Path) -> int:
    skill_md = skill_dir / "SKILL.md"
    if not skill_md.is_file():
        raise BuildError("required author-maintained skill is missing: {}".format(skill_md))
    fields = parse_skill_frontmatter(skill_md)
    if fields.get("name") != skill_dir.name:
        raise BuildError(
            "{} frontmatter name must match its directory ({})".format(skill_md, skill_dir.name)
        )
    description = fields.get("description", "")
    if not description:
        raise BuildError("{} frontmatter must include a description".format(skill_md))
    if len(description) > 1024:
        raise BuildError("{} frontmatter description exceeds 1024 characters".format(skill_md))

    files = _skill_files(skill_dir)
    if len(files) > MAX_FILES_PER_SKILL:
        raise BuildError("{} has {} files; the per-skill maximum is 100".format(skill_dir, len(files)))
    skill_md_size = skill_md.stat().st_size
    if skill_md_size > MAX_SKILL_MD_BYTES:
        raise BuildError("{} exceeds the 256 KiB SKILL.md limit".format(skill_md))
    total_bytes = 0
    for path in files:
        size = path.stat().st_size
        if path != skill_md and size > MAX_SUPPORTING_FILE_BYTES:
            raise BuildError("{} exceeds the 1 MiB per-file limit".format(path))
        total_bytes += size
    if total_bytes > MAX_SKILL_BYTES:
        raise BuildError("{} exceeds the 5 MiB per-skill limit".format(skill_dir))
    return total_bytes


def _copy_files(source: Path, destination: Path, *, suffix: str | None = None) -> list[Path]:
    copied = []
    for path in sorted(source.rglob("*")):
        if not path.is_file() or "__pycache__" in path.parts or path.suffix == ".pyc":
            continue
        if suffix is not None and path.suffix.casefold() != suffix.casefold():
            continue
        relative = path.relative_to(source)
        target = destination / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, target)
        copied.append(target)
    return copied


def _replace_base_url(source: Path, destination: Path, base_url: str) -> dict[str, Any]:
    try:
        value = json.loads(source.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise BuildError("could not read {}: {}".format(source, error)) from error
    rendered = json.dumps(value, ensure_ascii=False, indent=2).replace("{BASE_URL}", base_url.rstrip("/"))
    try:
        result = json.loads(rendered)
    except json.JSONDecodeError as error:
        raise BuildError("placeholder replacement produced invalid JSON in {}".format(source)) from error
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return result


def _validate_plugin_manifest(manifest: dict[str, Any], base_url: str) -> None:
    if manifest.get("$schema") != "https://agent-plugins.org/schemas/1.0.0/plugin.schema.json":
        raise BuildError("plugin.json must use the Agent Plugins 1.0.0 schema")
    if manifest.get("name") != SKILL_NAME:
        raise BuildError("plugin.json name must be {}".format(SKILL_NAME))
    extension = (manifest.get("extensions") or {}).get("com.openai") or {}
    interface = extension.get("interface") or {}
    if interface.get("displayName") != "Berlin Job Search":
        raise BuildError("plugin.json must declare the Berlin Job Search display name")
    if len(str(interface.get("shortDescription") or "")) > 30:
        raise BuildError("OpenAI plugin shortDescription must be 30 characters or less")
    category = str(interface.get("category") or "").casefold().replace("_", " ")
    if category not in OPENAI_CATEGORIES:
        raise BuildError("unsupported OpenAI plugin category: {}".format(interface.get("category")))
    prompts = interface.get("defaultPrompt") or []
    if len(prompts) > 3:
        raise BuildError("OpenAI plugin submission supports at most three default prompts")
    if extension.get("onboardingSkill") != "./skills/setup/SKILL.md":
        raise BuildError("onboardingSkill must point to ./skills/setup/SKILL.md")
    for field in ("websiteURL", "privacyPolicyURL", "termsOfServiceURL"):
        value = interface.get(field)
        if not isinstance(value, str) or "{BASE_URL}" in value or not value.startswith(base_url):
            raise BuildError("plugin.json {} must be an absolute URL using --base-url".format(field))


def _validate_mcp_manifest(manifest: dict[str, Any], base_url: str) -> None:
    if manifest.get("$schema") != "https://agent-plugins.org/schemas/1.0.0/mcp.schema.json":
        raise BuildError("mcp.json must include the Agent Plugins 1.0.0 MCP schema")
    if set(manifest) != {"$schema", "mcpServers"}:
        raise BuildError("mcp.json may contain only $schema and mcpServers")
    server = (manifest.get("mcpServers") or {}).get(SKILL_NAME) or {}
    if server.get("type") != "streamable-http":
        raise BuildError("mcpServers.{} must use streamable-http".format(SKILL_NAME))
    if server.get("url") != base_url.rstrip("/") + "/mcp":
        raise BuildError("mcpServers.{} URL must use --base-url and end with /mcp".format(SKILL_NAME))


def build_plugin(base_url: str, out: Path, repo_root: Path = ROOT) -> tuple[Path, Path]:
    parsed = urlsplit(base_url)
    if parsed.scheme != "https" or not parsed.netloc or parsed.username or parsed.password or parsed.fragment:
        raise BuildError("--base-url must be an absolute HTTPS origin or path without credentials or a fragment")
    base_url = base_url.rstrip("/")
    plugin_source = repo_root / "chatgpt" / "plugin-src"
    required = [
        plugin_source / "plugin.json",
        plugin_source / "mcp.json",
        plugin_source / "assets" / "logo.png",
        plugin_source / "assets" / "icon.png",
        plugin_source / "skills" / "setup" / "SKILL.md",
        plugin_source / "skills" / SKILL_NAME / "SKILL.md",
    ]
    missing = [path for path in required if not path.is_file()]
    if missing:
        raise BuildError("required plugin source is missing: {}".format(", ".join(map(str, missing))))

    output_dir = out.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    package_dir = output_dir / PLUGIN_FOLDER
    archive_path = output_dir / (PLUGIN_FOLDER + ".zip")

    with tempfile.TemporaryDirectory(prefix="gjs-plugin-build-") as temp_dir:
        staged = Path(temp_dir) / PLUGIN_FOLDER
        staged.mkdir()
        plugin_manifest = _replace_base_url(
            plugin_source / "plugin.json", staged / "plugin.json", base_url,
        )
        mcp_manifest = _replace_base_url(
            plugin_source / "mcp.json", staged / "mcp.json", base_url,
        )
        _validate_plugin_manifest(plugin_manifest, base_url)
        _validate_mcp_manifest(mcp_manifest, base_url)

        for name in ("logo.png", "icon.png"):
            target = staged / "assets" / name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(plugin_source / "assets" / name, target)

        setup_source = plugin_source / "skills" / "setup"
        setup_target = staged / "skills" / "setup"
        _copy_files(setup_source, setup_target)

        skill_source = plugin_source / "skills" / SKILL_NAME
        skill_target = staged / "skills" / SKILL_NAME
        skill_target.mkdir(parents=True, exist_ok=True)
        shutil.copy2(skill_source / "SKILL.md", skill_target / "SKILL.md")
        reference_source = repo_root / "skills" / SKILL_NAME / "references"
        asset_source = repo_root / "skills" / SKILL_NAME / "assets"
        if not reference_source.is_dir() or not asset_source.is_dir():
            raise BuildError("main skill references/ and assets/ directories are required")
        _copy_files(reference_source, skill_target / "references", suffix=".md")
        _copy_files(asset_source, skill_target / "assets")
        scripts_source = repo_root / "skills" / SKILL_NAME / "scripts"
        for filename in OFFLINE_SCRIPTS:
            source_file = scripts_source / filename
            if not source_file.is_file():
                raise BuildError("required offline skill script is missing: {}".format(source_file))
            target = skill_target / "scripts" / filename
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source_file, target)

        files = [path for path in staged.rglob("*") if path.is_file()]
        skill_dirs = [staged / "skills" / "setup", skill_target]
        if len(skill_dirs) > MAX_SKILLS:
            raise BuildError("the package contains more than five skills")
        combined_skill_bytes = sum(validate_skill(path) for path in skill_dirs)
        if combined_skill_bytes > MAX_ALL_SKILLS_BYTES:
            raise BuildError("the combined skills exceed the 8 MiB import limit")
        skill_archive = io.BytesIO()
        with zipfile.ZipFile(skill_archive, "w", compression=zipfile.ZIP_DEFLATED) as archive:
            for skill_dir in skill_dirs:
                for path in _skill_files(skill_dir):
                    archive.write(path, path.relative_to(staged / "skills"))
        if skill_archive.tell() > MAX_ALL_SKILLS_BYTES:
            raise BuildError("the combined compressed skill archive exceeds the 8 MiB import limit")
        for path in files:
            if path.suffix == ".pyc" or "__pycache__" in path.parts:
                raise BuildError("generated package must not contain Python bytecode")

        if package_dir.exists():
            for path in staged.rglob("*"):
                if not path.is_file():
                    continue
                target = package_dir / path.relative_to(staged)
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(path, target)
        else:
            shutil.copytree(staged, package_dir)

        with zipfile.ZipFile(archive_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
            for path in sorted(files):
                archive.write(path, Path(PLUGIN_FOLDER) / path.relative_to(staged))

    return package_dir, archive_path


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Build the Berlin Job Search portable ChatGPT plugin package.")
    parser.add_argument("--base-url", required=True, help="Public HTTPS origin for the hosted MCP server")
    parser.add_argument("--out", default="dist/", help="Output directory (default: dist/)")
    args = parser.parse_args(argv)
    try:
        package_dir, archive_path = build_plugin(args.base_url, Path(args.out))
    except (BuildError, OSError, ValueError) as error:
        print("error: {}".format(error), file=sys.stderr)
        return 2
    print("Package: {}".format(package_dir))
    print("Zip: {}".format(archive_path))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
