import sys

def calculate_reimbursement(trip_duration_days, miles_traveled, total_receipts_amount):
    """Calculates the reimbursement amount based on baseline rules."""

    # Rule 1: Base Per Diem (Initial)
    per_diem_reimbursement = trip_duration_days * 100.00

    # Rule 2 & 3: Tiered Mileage Reimbursement
    # Tier 1: First 100 miles at $0.58/mile
    # Tier 2: Miles above 100 at $0.29/mile (initial placeholder rate)
    tier1_threshold_miles = 100.0
    tier1_rate = 0.58
    tier2_rate = 0.48  # Refined based on Marcus's 600-mile trip hint

    if miles_traveled <= tier1_threshold_miles:
        mileage_reimbursement = miles_traveled * tier1_rate
    else:
        mileage_reimbursement = (tier1_threshold_miles * tier1_rate) + \
                                ((miles_traveled - tier1_threshold_miles) * tier2_rate)

    # Rule for Receipts: Flat 20% reimbursement
    # This is the best performing model so far (avg error ~$265).
    # Future iterations will explore more complex tiered/capped models based on interview hints.
    receipt_reimbursement = total_receipts_amount * 0.20

    total_reimbursement = per_diem_reimbursement + mileage_reimbursement + receipt_reimbursement

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
