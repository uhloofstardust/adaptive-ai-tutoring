"""Run every test module.   python -m tests"""
import subprocess
import sys

MODULES = ["test_core", "test_bkt_validation", "test_framework"]

failed = []
for m in MODULES:
    print(f"\n######## {m}", flush=True)
    if subprocess.call([sys.executable, "-m", f"tests.{m}"]) != 0:
        failed.append(m)
print("\n" + ("FAILED: " + ", ".join(failed) if failed else "ALL TEST MODULES PASSED"))
sys.exit(1 if failed else 0)
