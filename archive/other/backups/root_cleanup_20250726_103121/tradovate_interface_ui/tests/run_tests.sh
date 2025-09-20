#!/bin/bash

# Change to the project root directory
cd "$(dirname "$0")/.."

# Set up Python environment if using venv
if [ -d "venv" ]; then
    echo "Activating virtual environment..."
    source venv/bin/activate
fi

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}===========================================================${NC}"
echo -e "${BLUE}     RUNNING TESTS FOR ACCOUNT PHASE & SIZE MATRIX         ${NC}"
echo -e "${BLUE}===========================================================${NC}"

# Run the backend tests
echo -e "\n${BLUE}Running Python backend tests...${NC}"
python -m unittest tests/test_account_phase_size_matrix.py -v
PYTHON_RESULT=$?

if [ $PYTHON_RESULT -eq 0 ]; then
    echo -e "\n${GREEN}✅ Python tests PASSED${NC}"
else
    echo -e "\n${RED}❌ Python tests FAILED${NC}"
fi

# Open the JavaScript tests
echo -e "\n${BLUE}Frontend JavaScript tests:${NC}"
echo -e "To run these tests, open the file below in your browser:"
echo -e "${BLUE}file://$PWD/tests/run_js_tests.html${NC}"
echo -e "Then click the 'Run Tests' button on the page."

# Return to original directory
cd - > /dev/null

exit $PYTHON_RESULT