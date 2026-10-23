from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NAME_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
GENERATED_PREFIX = "generated from commands/"


class CommandSyncError(ValueError):
    pass


def parse_source(path: Path) -> tuple[dict[str, str], str]:
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        raise CommandSyncError("{} must start with YAML frontmatter".format(path))
    end = next((index for index in range(1, len(lines)) if lines[index].strip() == "---"), None)
    if end is None:
        raise CommandSyncError("{} has an unclosed frontmatter block".format(path))
    metadata: dict[str, str] = {}
    for line in lines[1:end]:
        key, separator, value = line.partition(":")
        if separator:
            metadata[key.strip()] = value.strip()
    if not metadata.get("description"):
        raise CommandSyncError("{} must have a description".format(path))
    if not metadata.get("argument-hint"):
        raise CommandSyncError("{} must have an argument-hint".format(path))
    body = "\n".join(lines[end + 1:]).lstrip("\n").rstrip()
    return metadata, body


def _claude_markdown(source: Path, metadata: dict[str, str], body: str) -> str:
    comment = "# {}{}, do not edit.\n".format(GENERATED_PREFIX, source.name)
    return "---\n{}description: {}\nargument-hint: {}\n---\n\n{}\n".format(
        comment, metadata["description"], metadata["argument-hint"], body,
    )


def _opencode_markdown(source: Path, metadata: dict[str, str], body: str) -> str:
    comment = "# {}{}, do not edit.\n".format(GENERATED_PREFIX, source.name)
    return "---\n{}description: {}\n---\n\n{}\n".format(
        comment, metadata["description"], body,
    )


def _toml_string(value: str) -> str:
    return '"' + value.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n") + '"'


def _gemini_toml(source: Path, metadata: dict[str, str], body: str) -> str:
    prompt = body.replace("$ARGUMENTS", "{{args}}").replace("\\", "\\\\").replace('"""', '\\"""')
    comment = "# {}{}, do not edit.\n".format(GENERATED_PREFIX, source.name)
    return comment + "description = {}\n".format(_toml_string(metadata["description"])) + 'prompt = """\n{}\n"""\n'.format(prompt)


def expected_outputs(source_dir: Path, repo_root: Path) -> dict[Path, str]:
    sources = sorted(source_dir.glob("*.md"))
    if not sources:
        raise CommandSyncError("no source commands found in {}".format(source_dir))
    expected: dict[Path, str] = {}
    for source in sources:
        if not NAME_PATTERN.fullmatch(source.stem):
            raise CommandSyncError("command names must use lowercase letters and hyphens: {}".format(source.name))
        metadata, body = parse_source(source)
        expected[repo_root / ".claude" / "commands" / (source.stem + ".md")] = _claude_markdown(source, metadata, body)
        expected[repo_root / ".opencode" / "commands" / (source.stem + ".md")] = _opencode_markdown(source, metadata, body)
        expected[repo_root / ".gemini" / "commands" / (source.stem + ".toml")] = _gemini_toml(source, metadata, body)
    return expected


def generated_stale_files(expected_paths: set[Path], repo_root: Path) -> list[Path]:
    stale = []
    for directory, suffix in (
        (repo_root / ".claude" / "commands", ".md"),
        (repo_root / ".opencode" / "commands", ".md"),
        (repo_root / ".gemini" / "commands", ".toml"),
    ):
        if not directory.is_dir():
            continue
        for path in directory.glob("*" + suffix):
            if path in expected_paths:
                continue
            try:
                first_lines = path.read_text(encoding="utf-8").splitlines()[:3]
            except (OSError, UnicodeError):
                continue
            if any(GENERATED_PREFIX in line for line in first_lines):
                stale.append(path)
    return stale


def sync_commands(
    source_dir: Path = ROOT / "commands",
    repo_root: Path = ROOT,
    *,
    check: bool = False,
) -> list[str]:
    try:
        expected = expected_outputs(source_dir, repo_root)
    except (OSError, UnicodeError, CommandSyncError) as error:
        return [str(error)]
    errors = []
    for path, content in expected.items():
        if check:
            if not path.is_file():
                errors.append("missing generated command: {}".format(path.relative_to(repo_root)))
            else:
                try:
                    actual = path.read_text(encoding="utf-8")
                except (OSError, UnicodeError) as error:
                    errors.append("{}: {}".format(path.relative_to(repo_root), error))
                else:
                    if actual != content:
                        errors.append("out of sync: {}".format(path.relative_to(repo_root)))
            continue
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
    if check:
        errors.extend(
            "stale generated command: {}".format(path.relative_to(repo_root))
            for path in generated_stale_files(set(expected), repo_root)
        )
    return errors


def check_commands(repo_root: Path = ROOT) -> list[str]:
    return sync_commands(repo_root / "commands", repo_root, check=True)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Generate Claude Code, OpenCode and Gemini CLI command files.")
    parser.add_argument("--check", action="store_true", help="Fail if generated files are missing or out of sync")
    args = parser.parse_args(argv)
    errors = sync_commands(check=args.check)
    if errors:
        for error in errors:
            print("ERROR: {}".format(error), file=sys.stderr)
        return 1
    print("Command files are in sync." if args.check else "Generated command files for Claude Code, OpenCode and Gemini CLI.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
