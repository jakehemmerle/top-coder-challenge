import sys

DEFAULT_PARAMS = {
    "per_diem_rate": 73.7227,
    "mileage_t1_threshold_miles": 107.7229,
    "mileage_t1_rate": 0.6605,
    "mileage_t2_threshold_miles": 429.7346,
    "mileage_t2_rate": 0.3057,
    "mileage_t3_rate": 0.2267,
    "receipt_reimbursement_rate": 0.4378,
    "five_day_trip_bonus_amount": 71.1104,
    "mileage_efficiency_threshold_miles_per_day": 102.6377,
    "mileage_efficiency_bonus_amount": 111.9857,
    "short_trip_day_threshold": 2,
    "low_mileage_threshold_miles": 61,
    "low_reimbursement_multiplier": 0.7834
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

    # Rule for Receipts: Flat 20% reimbursement on rounded amount
    # Rule #5: Receipt Rounding Quirks - Apply standard rounding to total_receipts_amount
    # This is the best performing model so far (avg error ~$263.76 with 5-day bonus).
    # Future iterations will explore more complex tiered/capped models based on interview hints.
    rounded_total_receipts = int(total_receipts_amount + 0.5) # Standard rounding
    receipt_reimbursement = rounded_total_receipts * params["receipt_reimbursement_rate"]

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
