import sys, warnings
warnings.filterwarnings("ignore")
sys.path.insert(0, ".")

from app.auth import verify_login, ROLES

tests = [
    ("admin",    "Admin@2026",    "admin"),
    ("siddique", "Siddique@2026", "admin"),
    ("manager1", "Manager@2026",  "manager"),
    ("analyst1", "Analyst@2026",  "analyst"),
    ("viewer1",  "Viewer@2026",   "viewer"),
    ("baduser",  "wrongpass",     None),
]

all_ok = True
for u, p, expected in tests:
    result = verify_login(u, p)
    got = result["role"] if result else None
    ok  = (got == expected)
    if not ok: all_ok = False
    status = "PASS" if ok else "FAIL"
    print(f"  {status}  {u:<12}  expected={expected}  got={got}")

print()
for rk, rv in ROLES.items():
    pages = rv["pages"]
    icon  = rv["icon"]
    label = rv["label"]
    print(f"  {icon} {label:<16}  pages={pages}")

print()
print("Auth OK!" if all_ok else "Auth FAILED")
