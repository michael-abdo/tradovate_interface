import subprocess
import sys
import os

# Change to project directory
os.chdir('/Users/Mike/trading/algos/EOD')

# Run the scraping script
result = subprocess.run([sys.executable, 'run_barchart_scrape.py'], capture_output=True, text=True)

print("STDOUT:")
print(result.stdout)
print("\nSTDERR:")
print(result.stderr)
print(f"\nReturn code: {result.returncode}")