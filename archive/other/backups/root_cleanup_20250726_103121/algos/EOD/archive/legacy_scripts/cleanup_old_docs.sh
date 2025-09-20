#!/bin/bash
# Cleanup old documentation files

echo "Removing old expected value analysis files..."
rm -f /Users/Mike/trading/algos/EOD/docs/analysis/expected_value_analysis/README.md
rm -f /Users/Mike/trading/algos/EOD/docs/analysis/expected_value_analysis/nq_ev_pseudocode.txt

echo "Removing old risk analysis files..."
rm -f /Users/Mike/trading/algos/EOD/docs/analysis/risk_analysis/README.md
rm -f /Users/Mike/trading/algos/EOD/docs/analysis/risk_analysis/risk_analysis.txt

echo "Cleanup complete!"