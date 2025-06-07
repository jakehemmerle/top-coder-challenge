import sys
import math

DEFAULT_PARAMS = {
    "per_diem_rate": 84.7402,
    "mileage_t1_threshold_miles": 132.2898,
    "mileage_t1_rate": 0.5153,
    "mileage_t2_threshold_miles": 415.7941,
    "mileage_t2_rate": 0.3304,
    "mileage_t3_rate": 0.2522,
    # "receipt_reimbursement_rate": 0.4378, # Replaced by tiered system
    "receipt_t1_threshold_amount": 524.2149,
    "receipt_t1_rate": 0.4226,
    "receipt_t2_threshold_amount": 1185.7473, # Amounts from t1_thresh to t2_thresh are Tier 2
    "receipt_t2_rate": 0.7472,
    "receipt_t3_rate": 0.1286, # Amounts above t2_thresh are Tier 3
    "five_day_trip_bonus_amount": 92.4952,
    "mileage_efficiency_threshold_miles_per_day": 246.0342,
    "mileage_efficiency_bonus_amount": 139.3399,
    "short_trip_day_threshold": 2,
    "low_mileage_threshold_miles": 93,
    "low_reimbursement_multiplier": 0.9373,
    "receipt_reimbursement_cap_amount": 750.0 # Max amount for receipt reimbursement - manually set
}

def calculate_reimbursement(trip_duration_days, miles_traveled, total_receipts_amount, params=DEFAULT_PARAMS):
    """Calculates the reimbursement amount based on baseline rules."""

    # Rule 1: Base Per Diem (Initial)
    per_diem_reimbursement = trip_duration_days * params["per_diem_rate"]

    # Rule 2, 3 & New: 3-Tier Mileage Reimbursement
    # Tier 1: Up to mileage_t1_threshold_miles (e.g., 100 miles) at mileage_t1_rate (e.g., $0.58/mile)
    # Tier 2: Miles between mileage_t1_threshold_miles and mileage_t2_threshold_miles (e.g., 100.01 to 500 miles) at mileage_t2_rate (e.g., $0.30/mile)
    # Tier 3: Miles above mileage_t2_threshold_miles (e.g., >500 miles) at mileage_t3_rate (e.g., $0.20/mile)
    mileage_reimbursement = 0.0
    if miles_traveled <= 0: # Handle zero or negative miles explicitly
        mileage_reimbursement = 0.0
    elif miles_traveled <= params["mileage_t1_threshold_miles"]:
        mileage_reimbursement = miles_traveled * params["mileage_t1_rate"]
    elif miles_traveled <= params["mileage_t2_threshold_miles"]:
        mileage_reimbursement = (params["mileage_t1_threshold_miles"] * params["mileage_t1_rate"]) + \
                                ((miles_traveled - params["mileage_t1_threshold_miles"]) * params["mileage_t2_rate"])
    else: # miles_traveled > params["mileage_t2_threshold_miles"]
        mileage_reimbursement = (params["mileage_t1_threshold_miles"] * params["mileage_t1_rate"]) + \
                                ((params["mileage_t2_threshold_miles"] - params["mileage_t1_threshold_miles"]) * params["mileage_t2_rate"]) + \
                                ((miles_traveled - params["mileage_t2_threshold_miles"]) * params["mileage_t3_rate"]) 

    # Receipt Reimbursement - with specific rounding quirks
    # Based on interview: "If your receipts end in 49 or 99 cents, you often get a little extra money."
    # This means for .49 or .99 cents, we ceil(); otherwise, we trunc().
    cents_val = round((total_receipts_amount - math.trunc(total_receipts_amount)) * 100)
    if cents_val == 49 or cents_val == 99:
        rounded_receipts_amount = math.ceil(total_receipts_amount)
    else:
        rounded_receipts_amount = math.trunc(total_receipts_amount)

    # 3-Tier Receipt Reimbursement
    if rounded_receipts_amount <= 0:
        receipt_reimbursement = 0.0
    elif rounded_receipts_amount <= params["receipt_t1_threshold_amount"]:
        receipt_reimbursement = rounded_receipts_amount * params["receipt_t1_rate"]
    elif rounded_receipts_amount <= params["receipt_t2_threshold_amount"]:
        receipt_reimbursement = (params["receipt_t1_threshold_amount"] * params["receipt_t1_rate"]) + \
                                ((rounded_receipts_amount - params["receipt_t1_threshold_amount"]) * params["receipt_t2_rate"])
    else: # Above receipt_t2_threshold_amount
        receipt_reimbursement = (params["receipt_t1_threshold_amount"] * params["receipt_t1_rate"]) + \
                                ((params["receipt_t2_threshold_amount"] - params["receipt_t1_threshold_amount"]) * params["receipt_t2_rate"]) + \
                                ((rounded_receipts_amount - params["receipt_t2_threshold_amount"]) * params["receipt_t3_rate"])

    # Apply cap to receipt reimbursement
    receipt_reimbursement = min(receipt_reimbursement, params["receipt_reimbursement_cap_amount"])

    total_reimbursement = per_diem_reimbursement + mileage_reimbursement + receipt_reimbursement

    # Rule #4: 5-Day Trip Bonus (Hypothesis)
    if trip_duration_days == 5:
        total_reimbursement += params["five_day_trip_bonus_amount"]

    # Rule #7: Efficiency Bonus (Mileage Related)
    # If miles_traveled / trip_duration_days > 150, add $50 bonus
    if trip_duration_days > 0:
        miles_per_day = miles_traveled / float(trip_duration_days) # Ensure float division
        if miles_per_day > params["mileage_efficiency_threshold_miles_per_day"]:
            total_reimbursement += params["mileage_efficiency_bonus_amount"]

    # Rule #8: Short Trip / Low Mileage Penalty
    if trip_duration_days <= params["short_trip_day_threshold"] and \
       miles_traveled <= params["low_mileage_threshold_miles"]:
        total_reimbursement *= params["low_reimbursement_multiplier"]

    return total_reimbursement

if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Usage: python calculate_reimbursement.py <trip_duration_days> <miles_traveled> <total_receipts_amount>", file=sys.stderr)
        sys.exit(1)

    try:
        trip_duration_days_arg = int(sys.argv[1])
        miles_traveled_arg = float(sys.argv[2])
        total_receipts_amount_arg = float(sys.argv[3])
    except ValueError:
        print(f"Error: Invalid input types. Args received: '{sys.argv[1]}', '{sys.argv[2]}', '{sys.argv[3]}'. Ensure days is an integer, and miles and receipts amount are floats.", file=sys.stderr)
        sys.exit(1)

    reimbursement = calculate_reimbursement(trip_duration_days_arg, miles_traveled_arg, total_receipts_amount_arg)
    
    # Output must be a single number rounded to 2 decimal places
    print(f"{reimbursement:.2f}")
