"""Quick syntax check on all page_modules."""
import sys, ast
from pathlib import Path
errors = []
for f in sorted(Path("page_modules").glob("p*.py")):
    try:
        ast.parse(f.read_text(encoding="utf-8"))
        print(f"  OK  {f.name}")
    except SyntaxError as e:
        print(f"  FAIL {f.name}: {e}")
        errors.append(f.name)
print(f"\n{'All OK!' if not errors else f'{len(errors)} files have errors'}")
