#!/bin/bash

# Ensure three arguments are provided
if [ "$#" -ne 3 ]; then
    echo "Usage: ./run.sh <trip_duration_days> <miles_traveled> <total_receipts_amount>" >&2
    exit 1
fi

TRIP_DURATION_DAYS=$1
MILES_TRAVELED=$2
TOTAL_RECEIPTS_AMOUNT=$3

# Execute the Python script
# Assuming the python script is in the strategy1_interview_driven subdirectory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" &> /dev/null && pwd)"
PYTHON_SCRIPT_PATH="$SCRIPT_DIR/strategy1_interview_driven/calculate_reimbursement.py"

if [ ! -f "$PYTHON_SCRIPT_PATH" ]; then
    echo "Error: Python script not found at $PYTHON_SCRIPT_PATH" >&2
    exit 1
fi

python3 "$PYTHON_SCRIPT_PATH" "$TRIP_DURATION_DAYS" "$MILES_TRAVELED" "$TOTAL_RECEIPTS_AMOUNT"