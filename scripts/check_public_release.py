"""Check the exact Git index for common accidental disclosures. No file contents are printed.

This heuristic guard complements manual review; it does not establish legal clearance
or detect every possible secret. Commit only after checking the index with this command.
"""
from pathlib import Path, PurePosixPath
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
ALLOWED_ROOT_FILES = {
    ".env.example", ".gitignore", ".gitattributes", "README.md", "README.zh-CN.md",
    "SECURITY.md", "requirements.in", "requirements.txt", "setup.cmd", "start.cmd", "stop.cmd",
}
ALLOWED_TREES = {
    "backend": {".py"}, "tests": {".py"}, "scripts": {".py", ".ps1"},
    "docs": {".md"}, "examples": {".json"}, ".github/workflows": {".yml", ".yaml"},
}
SECRET_PATTERNS = {
    "private key": re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    "provider token": re.compile(r"\b(?:sk-(?:proj-|svcacct-)?[A-Za-z0-9_-]{24,}|gh[pousr]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{40,}|AKIA[A-Z0-9]{16})\b"),
    "personal Windows path": re.compile(r"[A-Za-z]:[\\/]+Users[\\/]+(?!Public\b)[^\s\\/]+", re.I),
    "personal Unix path": re.compile(r"/(?:Users|home)/[A-Za-z0-9_.-]+/"),
    "non-loopback private address": re.compile(r"(?<![\d.])(?:10\.(?:\d{1,3}\.){2}\d{1,3}|192\.168\.\d{1,3}\.\d{1,3}|172\.(?:1[6-9]|2\d|3[01])\.\d{1,3}\.\d{1,3})(?![\d.])"),
}


def inspect_file(name: str, content: bytes, mode: str = "100644") -> list[str]:
    path = PurePosixPath(name)
    problems = []
    if mode not in {"100644", "100755"}:
        problems.append("symlink or submodule not allowed")
    if name not in ALLOWED_ROOT_FILES and not any(
        name.startswith(prefix + "/") and path.suffix in suffixes
        for prefix, suffixes in ALLOWED_TREES.items()
    ):
        problems.append("outside the public-file allowlist")
    if any(part.startswith(".") for part in path.parts[1:]):
        problems.append("hidden nested file")
    if len(content) > 512_000:
        problems.append("unexpectedly large file")
    try:
        text = content.decode("utf-8")
    except UnicodeDecodeError:
        return problems + ["non-UTF-8 or binary content"]
    if "\x00" in text:
        problems.append("binary content")
    for label, pattern in SECRET_PATTERNS.items():
        if pattern.search(text):
            problems.append(label)
    if name == ".env.example":
        for line in text.splitlines():
            if line.strip() and not line.lstrip().startswith("#"):
                key, sep, value = line.partition("=")
                if not sep or value.strip():
                    problems.append("environment example must contain empty assignments only")
    return problems


def git(*args: str) -> bytes:
    return subprocess.check_output(["git", "-c", f"safe.directory={ROOT.as_posix()}", *args], cwd=ROOT)


def main() -> int:
    try:
        entries = git("ls-files", "--stage", "-z").split(b"\0")
    except (OSError, subprocess.CalledProcessError):
        print("FAIL: a Git checkout with staged or tracked files is required.")
        return 1
    failures = []
    checked = 0
    for entry in filter(None, entries):
        metadata, raw_name = entry.split(b"\t", 1)
        mode, object_id, stage = metadata.decode().split()
        name = raw_name.decode("utf-8")
        checked += 1
        content = git("cat-file", "blob", object_id)
        reasons = inspect_file(name, content, mode)
        if stage != "0":
            reasons.append("unresolved merge")
        failures.extend((name, reason) for reason in reasons)
    if not checked:
        print("FAIL: Git index is empty; stage the public files first.")
        return 1
    if failures:
        for name, reason in failures:
            print(f"FAIL: {name}: {reason}")
        return 1
    print(f"PASS: {checked} Git-index files checked; no configured disclosure patterns found.")
    print("Scope: index contents only. Manual review remains necessary.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
