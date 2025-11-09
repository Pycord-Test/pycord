#!/usr/bin/env python3
"""Check copyright headers in Python files."""

import sys
from pathlib import Path

MIT_HEADER = "The MIT License (MIT)\n\nCopyright (c) 2021-present Pycord Development"

# Files with non-MIT licenses
EXCEPTIONS = {
    "discord/utils/private.py": "CC-BY-SA 4.0",  # hybridmethod
    # Add more exceptions as needed
}


def check_file(filepath: Path) -> tuple[bool, str]:
    """
    Check if file has appropriate header.

    Returns:
        (is_valid, message)
    """
    relative_path = str(filepath.relative_to(Path.cwd()))

    try:
        content = filepath.read_text(encoding="utf-8")
    except Exception as e:
        return False, f"Error reading file: {e}"

    # Check if this is an exception file
    if relative_path in EXCEPTIONS:
        expected_license = EXCEPTIONS[relative_path]
        # Just verify it has SOME license header
        if "License" in content[:500] or "Copyright" in content[:500]:
            return True, f"OK (Exception: {expected_license})"
        return False, f"Missing license header (Expected: {expected_license})"

    # Check for standard MIT header
    if MIT_HEADER in content:
        return True, "OK (MIT)"

    return False, "Missing MIT license header"


def main():
    errors = []
    warnings = []

    print("Checking copyright headers...\n")

    for filepath in sorted(Path("discord").rglob("*.py")):
        # Skip common excluded directories
        if any(part in ["__pycache__", ".git", "venv", ".venv"] for part in filepath.parts):
            continue

        is_valid, message = check_file(filepath)
        relative_path = filepath.relative_to(Path.cwd())

        if not is_valid:
            errors.append((relative_path, message))
            print(f"❌ {relative_path}: {message}")
        elif "Exception" in message:
            warnings.append((relative_path, message))
            print(f"⚠️  {relative_path}: {message}")
        else:
            print(f"✓  {relative_path}: {message}")

    print("\n" + "=" * 60)

    if warnings:
        print(f"\n⚠️  {len(warnings)} file(s) with non-MIT licenses:")
        for path, msg in warnings:
            print(f"   - {path}")

    if errors:
        print(f"\n❌ {len(errors)} file(s) with issues:")
        for path, msg in errors:
            print(f"   - {path}: {msg}")
        sys.exit(1)
    else:
        print(f"\n✓ All {len(list(Path('discord').rglob('*.py')))} files have valid headers!")
        sys.exit(0)


if __name__ == "__main__":
    main()
