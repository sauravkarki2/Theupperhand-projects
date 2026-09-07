#!/usr/bin/env python3
"""Syntax-check every Python snippet in the knowledge base.

The modules are full of copy-pasteable bpy. A snippet that doesn't parse is
worse than no snippet, because you only find out at the keyboard mid-session.
This catches that in a second.

    python3 scripts/qa_snippets.py

Exits non-zero if anything fails to parse. Note this checks SYNTAX only — it
cannot verify that a bpy property name exists in your Blender version. That is
what the guarded `_set()` helper in build_beverage_ad.py is for.
"""
import ast
import glob
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FENCE = re.compile(r"```(?:python|py)\n(.*?)```", re.S)


def main():
    total = failures = 0
    targets = sorted(
        glob.glob(os.path.join(ROOT, "modules", "*.md"))
        + glob.glob(os.path.join(ROOT, "reference", "*.md"))
        + glob.glob(os.path.join(ROOT, "*.md"))
    )

    for path in targets:
        with open(path, encoding="utf-8") as handle:
            blocks = FENCE.findall(handle.read())
        if not blocks:
            continue
        bad = []
        for index, block in enumerate(blocks, 1):
            total += 1
            try:
                ast.parse(block)
            except SyntaxError as exc:
                bad.append((index, exc.lineno, exc.msg))
                failures += 1
        rel = os.path.relpath(path, ROOT)
        print("%-46s %2d blocks  %s"
              % (rel, len(blocks), "OK" if not bad else "%d FAIL" % len(bad)))
        for index, lineno, msg in bad:
            print("      block %d, line %s: %s" % (index, lineno, msg))

    # The build script itself.
    script = os.path.join(ROOT, "scripts", "build_beverage_ad.py")
    with open(script, encoding="utf-8") as handle:
        source = handle.read()
    try:
        ast.parse(source)
        print("%-46s %s" % ("scripts/build_beverage_ad.py",
                            "OK (%d lines)" % len(source.splitlines())))
    except SyntaxError as exc:
        print("scripts/build_beverage_ad.py FAILED line %s: %s"
              % (exc.lineno, exc.msg))
        failures += 1

    print("\n%d/%d snippets parse" % (total - failures, total))
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
