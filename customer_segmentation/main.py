"""
main.py - Run all scripts in sequence
Author : Bharath V
"""
import subprocess, sys, os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

scripts = [
    ("generate_data.py",    "Generating dataset..."),
    ("eda_analysis.py",     "Running EDA & Charts..."),
    ("rfm_segmentation.py", "Running RFM + K-Means Clustering..."),
    ("sql_analysis.py",     "Running SQL Analysis..."),
    ("dashboard.py",        "Building Dashboard..."),
    ("prepare_powerbi.py",  "Preparing Power BI Excel..."),
]

for script, msg in scripts:
    print("\n" + "="*50)
    print("  " + msg)
    print("="*50)
    result = subprocess.run([sys.executable, os.path.join(BASE_DIR, script)])
    if result.returncode != 0:
        print("Error in " + script)
        sys.exit(1)

print("\n  All done! Check the outputs/ folder.")
