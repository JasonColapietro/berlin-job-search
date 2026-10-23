from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from urllib.parse import unquote, urlsplit

try:
    from .sync_commands import check_commands, parse_source
except ImportError:
    from sync_commands import check_commands, parse_source

ROOT = Path(__file__).resolve().parents[1]
SKILL_NAME = "berlin-job-search"
NAME_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
RESOURCE_PATH_PATTERN = re.compile(r"(?<![\w.-])(?:references|assets|scripts)/[A-Za-z0-9_.@/-]+")
MARKDOWN_LINK_PATTERN = re.compile(r"!?\[[^\]]*\]\(([^)]+)\)")
SKILL_ROOTS = (
    (ROOT / "skills" / SKILL_NAME, True),
    (ROOT / "chatgpt" / "plugin-src" / "skills" / SKILL_NAME, True),
    (ROOT / "chatgpt" / "plugin-src" / "skills" / "setup", False),
)
VERSIONED_MANIFESTS = (
    ROOT / ".claude-plugin" / "plugin.json",
    ROOT / ".claude-plugin" / "marketplace.json",
    ROOT / ".codex-plugin" / "plugin.json",
    ROOT / "chatgpt" / "plugin-src" / "plugin.json",
)
SKILL_LINK_FALLBACKS = {
    ROOT / "chatgpt" / "plugin-src" / "skills" / SKILL_NAME: ROOT / "skills" / SKILL_NAME,
    ROOT / "chatgpt" / "plugin-src" / "skills" / "setup": ROOT / "skills" / SKILL_NAME,
}
FORBIDDEN_PATH_MARKERS = (bytes((47, 116, 109, 112, 47)), bytes((47, 85, 115, 101, 114, 115, 47)))


def parse_frontmatter(path: Path) -> tuple[dict[str, str], str]:
    content = path.read_text(encoding="utf-8")
    lines = content.splitlines()
    if not lines or lines[0].strip() != "---":
        raise ValueError("{} must start with YAML frontmatter".format(path.relative_to(ROOT)))
    end = next((index for index in range(1, len(lines)) if lines[index].strip() == "---"), None)
    if end is None:
        raise ValueError("{} has an unclosed YAML frontmatter block".format(path.relative_to(ROOT)))
    fields: dict[str, str] = {}
    current_parent = ""
    for line in lines[1:end]:
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        indentation = len(line) - len(line.lstrip())
        key, separator, value = stripped.partition(":")
        if not separator:
            continue
        if indentation == 0:
            current_parent = key
            if value.strip():
                fields[key] = value.strip().strip("\"'")
        elif current_parent == "metadata":
            fields["metadata." + key] = value.strip().strip("\"'")
    return fields, content


def validate_skill(skill_dir: Path, version: str) -> list[str]:
    errors: list[str] = []
    skill_md = skill_dir / "SKILL.md"
    if not skill_md.is_file():
        return ["missing required skill file: {}".format(skill_md.relative_to(ROOT))]
    try:
        frontmatter, content = parse_frontmatter(skill_md)
    except (OSError, UnicodeError, ValueError) as error:
        return [str(error)]
    relative = skill_md.relative_to(ROOT)
    name = frontmatter.get("name", "")
    description = frontmatter.get("description", "")
    if name != skill_dir.name:
        errors.append("{}: frontmatter name must match directory '{}'".format(relative, skill_dir.name))
    if not NAME_PATTERN.fullmatch(name):
        errors.append("{}: name must use lowercase letters, digits and hyphens".format(relative))
    if len(description) > 1024:
        errors.append("{}: description exceeds 1024 characters".format(relative))
    if not description:
        errors.append("{}: frontmatter description is required".format(relative))
    if len(content.splitlines()) > 500:
        errors.append("{}: SKILL.md exceeds 500 lines".format(relative))
    if "metadata.version" in frontmatter and frontmatter["metadata.version"] != version:
        errors.append(
            "{}: metadata.version is {}, expected {}".format(
                relative, frontmatter["metadata.version"], version,
            )
        )
    if skill_dir.name == SKILL_NAME and skill_md in {
        ROOT / "skills" / SKILL_NAME / "SKILL.md",
        ROOT / "chatgpt" / "plugin-src" / "skills" / SKILL_NAME / "SKILL.md",
    } and frontmatter.get("metadata.version") != version:
        errors.append("{}: metadata.version must equal VERSION".format(relative))

    resolution_root = SKILL_LINK_FALLBACKS.get(skill_dir, skill_dir)
    for reference in set(RESOURCE_PATH_PATTERN.findall(content)):
        clean = reference.rstrip(".,;:!?)]}`\"'")
        candidates = (skill_dir / clean, resolution_root / clean)
        if not any(candidate.exists() for candidate in candidates):
            errors.append("{}: referenced path does not exist: {}".format(relative, clean))
    return errors


def validate_json_files() -> list[str]:
    errors: list[str] = []
    excluded = {".git", "dist", "__pycache__"}
    for path in ROOT.rglob("*.json"):
        if excluded.intersection(path.relative_to(ROOT).parts):
            continue
        try:
            json.loads(path.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError) as error:
            errors.append("{}: invalid JSON ({})".format(path.relative_to(ROOT), error))
    return errors


def validate_manifest_versions(version: str) -> list[str]:
    errors: list[str] = []
    for path in VERSIONED_MANIFESTS:
        if not path.is_file():
            errors.append("missing manifest: {}".format(path.relative_to(ROOT)))
            continue
        try:
            manifest = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError) as error:
            errors.append("{}: invalid JSON ({})".format(path.relative_to(ROOT), error))
            continue
        if manifest.get("version") != version:
            errors.append(
                "{}: version is {!r}, expected {}".format(
                    path.relative_to(ROOT), manifest.get("version"), version,
                )
            )
        for plugin in manifest.get("plugins", []):
            if "version" in plugin and plugin["version"] != version:
                errors.append(
                    "{}: plugin entry version is {!r}, expected {}".format(
                        path.relative_to(ROOT), plugin["version"], version,
                    )
                )
    marketplace = ROOT / ".agents" / "plugins" / "marketplace.json"
    if marketplace.is_file():
        try:
            manifest = json.loads(marketplace.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError) as error:
            errors.append("{}: invalid JSON ({})".format(marketplace.relative_to(ROOT), error))
        else:
            for plugin in manifest.get("plugins", []):
                if "version" in plugin and plugin["version"] != version:
                    errors.append(
                        "{}: plugin entry version is {!r}, expected {}".format(
                            marketplace.relative_to(ROOT), plugin["version"], version,
                        )
                    )
    return errors


def validate_symlinks() -> list[str]:
    expected = {
        ROOT / ".agents" / "skills" / SKILL_NAME: "../../skills/berlin-job-search",
        ROOT / ".claude" / "skills" / SKILL_NAME: "../../skills/berlin-job-search",
    }
    errors = []
    target = (ROOT / "skills" / SKILL_NAME).resolve()
    for link, link_target in expected.items():
        if not link.is_symlink():
            errors.append("{}: expected a symlink".format(link.relative_to(ROOT)))
            continue
        if link.readlink().as_posix() != link_target:
            errors.append("{}: expected relative target {}".format(link.relative_to(ROOT), link_target))
        try:
            if link.resolve(strict=True) != target:
                errors.append("{}: symlink resolves to the wrong skill directory".format(link.relative_to(ROOT)))
        except OSError:
            errors.append("{}: symlink target does not resolve".format(link.relative_to(ROOT)))
    return errors


def validate_local_path_strings() -> list[str]:
    errors = []
    excluded = {".git", "dist", "__pycache__"}
    for path in ROOT.rglob("*"):
        if excluded.intersection(path.relative_to(ROOT).parts) or not path.is_file():
            continue
        try:
            data = path.read_bytes()
        except OSError as error:
            errors.append("{}: could not read for path check ({})".format(path.relative_to(ROOT), error))
            continue
        if any(marker in data for marker in FORBIDDEN_PATH_MARKERS):
            errors.append("{}: contains a local machine path".format(path.relative_to(ROOT)))
    return errors


def validate_readme_links() -> list[str]:
    errors: list[str] = []
    readmes = sorted(ROOT.glob("README*.md"))
    if not readmes:
        return ["missing README*.md files"]
    for readme in readmes:
        in_fence = False
        for line_number, line in enumerate(readme.read_text(encoding="utf-8").splitlines(), 1):
            if line.lstrip().startswith("```") or line.lstrip().startswith("~~~"):
                in_fence = not in_fence
                continue
            if in_fence:
                continue
            for match in MARKDOWN_LINK_PATTERN.finditer(line):
                target = match.group(1).strip()
                if target.startswith("<") and ">" in target:
                    target = target[1:target.index(">")]
                else:
                    target = target.split(None, 1)[0] if target else ""
                parsed = urlsplit(target)
                if parsed.scheme or parsed.netloc or not parsed.path:
                    continue
                relative_path = unquote(parsed.path)
                if relative_path.startswith("/"):
                    continue
                candidate = (readme.parent / relative_path).resolve()
                try:
                    candidate.relative_to(ROOT)
                except ValueError:
                    errors.append("{}:{}: link escapes repository: {}".format(readme.name, line_number, target))
                    continue
                if not candidate.exists():
                    errors.append("{}:{}: broken relative link: {}".format(readme.name, line_number, target))
    return errors


def validate_readme_summaries() -> list[str]:
    errors = []
    readme = ROOT / "README.md"
    if readme.is_file():
        english = readme.read_text(encoding="utf-8")
        for source in sorted((ROOT / "commands").glob("*.md")):
            try:
                metadata, _ = parse_source(source)
            except (OSError, UnicodeError, ValueError) as error:
                errors.append(str(error))
                continue
            if metadata["description"] not in english:
                errors.append("README.md: missing slash-command description from {}".format(source.name))
    return errors


def main() -> int:
    version_path = ROOT / "VERSION"
    errors: list[str] = []
    if not version_path.is_file():
        errors.append("missing VERSION file")
        version = ""
    else:
        version = version_path.read_text(encoding="utf-8").strip()
        if not version:
            errors.append("VERSION must not be empty")
    for skill_dir, require_version in SKILL_ROOTS:
        errors.extend(validate_skill(skill_dir, version))
        if require_version:
            skill_md = skill_dir / "SKILL.md"
            if skill_md.is_file():
                try:
                    fields, _ = parse_frontmatter(skill_md)
                    if fields.get("metadata.version") != version:
                        error = "{}: metadata.version must equal VERSION".format(skill_md.relative_to(ROOT))
                        if error not in errors:
                            errors.append(error)
                except (OSError, UnicodeError, ValueError):
                    pass
    errors.extend(validate_json_files())
    errors.extend(validate_manifest_versions(version))
    errors.extend(validate_symlinks())
    errors.extend(validate_local_path_strings())
    errors.extend(validate_readme_links())
    errors.extend(validate_readme_summaries())
    errors.extend(check_commands(ROOT))
    if errors:
        for error in errors:
            print("ERROR: {}".format(error), file=sys.stderr)
        print("Skill validation failed with {} error(s).".format(len(errors)), file=sys.stderr)
        return 1
    print("Skill validation passed for version {}.".format(version))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
