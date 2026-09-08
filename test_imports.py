"""Verify all page imports resolve correctly."""
import sys, warnings
warnings.filterwarnings("ignore")
sys.path.insert(0, ".")

pages = [
    "pages.p1_executive",
    "pages.p2_finance",
    "pages.p3_operations",
    "pages.p4_drivers",
    "pages.p5_fleet",
    "pages.p6_forecast",
    "pages.p7_map",
    "pages.p8_stories",
    "pages.p9_chat",
    "pages.p10_alerts",
]

for p in pages:
    try:
        import importlib
        importlib.import_module(p)
        print(f"  OK  {p}")
    except Exception as e:
        print(f"  FAIL {p}: {e}")

print("\nImport check complete.")
