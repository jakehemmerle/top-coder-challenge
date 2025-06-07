import sys

DEFAULT_PARAMS = {
    "per_diem_rate": 71.0531,
    "mileage_tier1_threshold_miles": 1369.1215,
    "mileage_tier1_rate": 0.4424,
    "mileage_tier2_rate": 0.3478,
    "receipt_reimbursement_rate": 0.4239, # For rounded receipts
    "five_day_trip_bonus_amount": 27.9537,
    "mileage_efficiency_threshold_miles_per_day": 110.5237,
    "mileage_efficiency_bonus_amount": 147.3527,
    "short_trip_day_threshold": 3,
    "low_mileage_threshold_miles": 34,
    "low_reimbursement_multiplier": 1.3979
}

def calculate_reimbursement(trip_duration_days, miles_traveled, total_receipts_amount, params=DEFAULT_PARAMS):
    """Calculates the reimbursement amount based on baseline rules."""

    # Rule 1: Base Per Diem (Initial)
    per_diem_reimbursement = trip_duration_days * params["per_diem_rate"]

    # Rule 2 & 3: Tiered Mileage Reimbursement
    # Tier 1: First 100 miles at $0.58/mile
    # Tier 2: Miles above 100 at $0.29/mile (initial placeholder rate)
    mileage_reimbursement = 0.0
    if miles_traveled <= params["mileage_tier1_threshold_miles"]:
        mileage_reimbursement = miles_traveled * params["mileage_tier1_rate"]
    else:
        mileage_reimbursement = (params["mileage_tier1_threshold_miles"] * params["mileage_tier1_rate"]) + \
                                ((miles_traveled - params["mileage_tier1_threshold_miles"]) * params["mileage_tier2_rate"]) 

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
