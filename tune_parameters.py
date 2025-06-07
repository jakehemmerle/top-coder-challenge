import sys
import os
import json
import re
import random
from multiprocessing import Pool, cpu_count
from functools import partial
import fileinput # For persisting best params at the end
import copy
from copy import deepcopy # Ensure deepcopy is available

# --- Configuration ---
# Assuming tune_parameters.py is in the root of top-coder-challenge
# and calculate_reimbursement.py is in strategy1_interview_driven/
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CALC_SCRIPT_MODULE_DIR = os.path.join(SCRIPT_DIR, "strategy1_interview_driven")
CALC_SCRIPT_FILE_NAME = "calculate_reimbursement.py"
CALC_SCRIPT_ABS_PATH = os.path.join(CALC_SCRIPT_MODULE_DIR, CALC_SCRIPT_FILE_NAME)
PUBLIC_CASES_JSON_PATH = os.path.join(SCRIPT_DIR, "public_cases.json")

# Define parameter ranges for random search [min, max, type ('float' or 'int')]
PARAMETER_RANGES = {
    "per_diem_rate": [70.00, 130.00, 'float'],
    "mileage_t1_threshold_miles": [80.0, 150.0, 'float'],
    "mileage_t1_rate": [0.50, 0.70, 'float'],
    "mileage_t2_threshold_miles": [300.0, 700.0, 'float'],
    "mileage_t2_rate": [0.20, 0.40, 'float'],
    "mileage_t3_rate": [0.10, 0.30, 'float'],
    # "receipt_reimbursement_rate": [0.10, 0.50, 'float'], # Replaced by tiered system
    "receipt_t1_threshold_amount": [400.0, 700.0, 'float'],
    "receipt_t1_rate": [0.20, 0.60, 'float'],
    "receipt_t2_threshold_amount": [700.0, 1200.0, 'float'],
    "receipt_t2_rate": [0.40, 0.80, 'float'], # Potential "sweet spot" rate
    "receipt_t3_rate": [0.05, 0.30, 'float'], # Diminishing returns rate
    "five_day_trip_bonus_amount": [0.00, 100.00, 'float'],
    "mileage_efficiency_threshold_miles_per_day": [100.0, 400.0, 'float'],
    "mileage_efficiency_bonus_amount": [0.00, 150.00, 'float'],
    "short_trip_day_threshold": [1, 3, 'int'],
    "low_mileage_threshold_miles": [10, 100, 'int'],
    "low_reimbursement_multiplier": [0.5, 1.5, 'float'],
}

# Add the directory of calculate_reimbursement.py to sys.path for import
if CALC_SCRIPT_MODULE_DIR not in sys.path:
    sys.path.insert(0, CALC_SCRIPT_MODULE_DIR)

# Import the target function and its default parameters
try:
    from calculate_reimbursement import calculate_reimbursement, DEFAULT_PARAMS
except ImportError as e:
    print(f"Error: Could not import 'calculate_reimbursement' or 'DEFAULT_PARAMS' from {CALC_SCRIPT_ABS_PATH}. Ensure the file exists and is importable. Error: {e}", file=sys.stderr)
    sys.exit(1)

# --- Helper Functions ---

def load_test_cases(json_path):
    """Loads test cases from the public_cases.json file."""
    try:
        with open(json_path, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Error: Test cases file not found at {json_path}", file=sys.stderr)
        return []
    except json.JSONDecodeError:
        print(f"Error: Could not decode JSON from {json_path}", file=sys.stderr)
        return []

def process_single_case(case, params_for_this_run):
    """Worker function to process a single test case with a given set of parameters."""
    try:
        input_data = case['input']
        case_id = case.get('id', 'N/A') # Get case ID from top level if available

        trip_duration = int(input_data['trip_duration_days'])
        miles_traveled = float(input_data['miles_traveled'])
        receipts_amount = float(input_data['total_receipts_amount'])
        expected_reimbursement = float(case['expected_output']) # Corrected key based on file structure

        # Call the imported calculation function with the specific params for this run
        calculated_reimbursement = calculate_reimbursement(
            trip_duration, miles_traveled, receipts_amount, params=params_for_this_run
        )
        error = abs(calculated_reimbursement - expected_reimbursement)
        return error
    except (KeyError, ValueError) as conversion_error:
        # This case is likely if JSON data is malformed or a key is missing for a specific entry
        print(f"Data conversion/KeyError for case ID {case_id if 'case_id' in locals() else case.get('id', 'N/A')}: {conversion_error}. \nCase data: {case}. \nInput data accessed: {input_data if 'input_data' in locals() else 'N/A'}", file=sys.stderr)
        return float('inf')
    except Exception as e:
        # This would be an error within calculate_reimbursement or other unexpected issue
        print(f"Unexpected error processing case ID {case_id if 'case_id' in locals() else case.get('id', 'N/A')}: {e}. \nCase data: {case}. \nParams sample: {params_for_this_run}", file=sys.stderr)
        return float('inf')

def perform_parallel_evaluation(params_to_test, all_test_cases):
    """Evaluates all test cases in parallel for a given set of parameters."""
    if not all_test_cases:
        return float('inf')

    num_processes = cpu_count()
    # Create a partial function to pass the fixed 'params_to_test' to the worker
    worker_func = partial(process_single_case, params_for_this_run=params_to_test)
    
    total_error = 0
    num_valid_cases = 0

    with Pool(processes=num_processes) as pool:
        results = pool.map(worker_func, all_test_cases)
    
    for error_value in results:
        if error_value != float('inf'):
            total_error += error_value
            num_valid_cases += 1
    
    if num_valid_cases == 0:
        return float('inf') # Avoid division by zero if all cases failed
    return total_error / num_valid_cases

def persist_best_params(param_name, best_value):
    """Modifies DEFAULT_PARAMS in calculate_reimbursement.py with the best found value."""
    try:
        if not os.path.exists(CALC_SCRIPT_ABS_PATH):
            print(f"Error: Calculation script not found at {CALC_SCRIPT_ABS_PATH} for persisting.", file=sys.stderr)
            return False

        str_best_value = f'\"{best_value}\"' if isinstance(best_value, str) else str(best_value)
        pattern = re.compile(r'("{}"\s*:\s*)(\S+)(,?)'.format(param_name))
        modified = False

        for line in fileinput.input(CALC_SCRIPT_ABS_PATH, inplace=True):
            match = pattern.search(line)
            if match:
                new_line = pattern.sub(r'\g<1>{}\g<3>'.format(str_best_value), line)
                sys.stdout.write(new_line)
                modified = True
            else:
                sys.stdout.write(line)
        
        if not modified:
            print(f"Warning: Parameter '{param_name}' not found for persisting in {CALC_SCRIPT_ABS_PATH}.", file=sys.stderr)
        return modified
    except Exception as e:
        print(f"Error persisting parameter {param_name} in {CALC_SCRIPT_ABS_PATH}: {e}", file=sys.stderr)
        return False

def evaluate_parameters(params_to_test, test_cases):
    num_processes = cpu_count()
    # print(f"Using up to {num_processes} processes for parallel evaluation.")
    
    with Pool(processes=num_processes) as pool:
        process_func = partial(process_single_case, params_for_this_run=params_to_test)
        errors = pool.map(process_func, test_cases)
    
    valid_errors = [e for e in errors if e != float('inf')]
    if not valid_errors:
        return float('inf')
    
    average_error = sum(valid_errors) / len(valid_errors)
    return average_error

def random_search_parameters(num_trials, test_cases, base_params):
    print(f"--- Random Search Parameter Tuning Initialized ---")
    print(f"Running {num_trials} random trials.\n")

    best_params_overall = None
    min_avg_error_overall = float('inf')

    for i in range(num_trials):
        candidate_params = deepcopy(base_params) # Start with base, then override with random
        print(f"Trial {i+1}/{num_trials}...")
        current_trial_param_details = {}
        for param_name, (min_val, max_val, param_type) in PARAMETER_RANGES.items():
            if param_type == 'float':
                random_value = random.uniform(min_val, max_val)
            elif param_type == 'int':
                random_value = random.randint(min_val, max_val)
            else:
                # Fallback for safety, though should not happen with defined ranges
                random_value = base_params.get(param_name, min_val) 
            candidate_params[param_name] = random_value
            current_trial_param_details[param_name] = random_value
        
        # print(f"  Testing with: {current_trial_param_details}") # Optional: print params for each trial
        average_error = evaluate_parameters(candidate_params, test_cases)
        print(f"  Average Error: {average_error:.4f}")

        if average_error < min_avg_error_overall:
            min_avg_error_overall = average_error
            best_params_overall = deepcopy(candidate_params)
            print(f"  ** New best error found: {min_avg_error_overall:.4f} **")

    print(f"\n--- Random Search Complete --- ")
    if best_params_overall:
        print(f"Best parameters found after {num_trials} trials with Average Error: {min_avg_error_overall:.4f}")
        print("Best parameter set:")
        for key, value in best_params_overall.items():
            # Format float values for readability
            if isinstance(value, float):
                print(f"  '{key}': {value:.4f}") 
            else:
                print(f"  '{key}': {value}")
        print(f"\nTo persist, manually update DEFAULT_PARAMS in {os.path.join(CALC_SCRIPT_MODULE_DIR, CALC_SCRIPT_FILE_NAME)} with these values.")
    else:
        print("No improvement found or all trials failed.")
    print("-------------------------------------")
    return best_params_overall, min_avg_error_overall

def tune_single_parameter(param_name, test_values, test_cases, base_params):
    print(f"--- Single Parameter Tuning Initialized ---")
    print(f"Tuning parameter: '{param_name}' in calculate_reimbursement.py")
    print(f"Testing values: {test_values}\n")

    results = {}
    min_avg_error = float('inf')
    best_value_for_param = None

    for value in test_values:
        print(f"Testing {param_name} = {value}...")
        current_params = deepcopy(base_params)
        current_params[param_name] = value
        
        average_error = evaluate_parameters(current_params, test_cases)
        results[value] = average_error
        print(f"  Average Error: {average_error:.4f}")

        if average_error < min_avg_error:
            min_avg_error = average_error
            best_value_for_param = value

    print(f"\n--- Tuning Complete for '{param_name}' ---")
    if best_value_for_param is not None:
        print(f"Best value found: {best_value_for_param} with Average Error: {min_avg_error:.4f}")
        print(f"To persist, manually update DEFAULT_PARAMS['{param_name}'] = {best_value_for_param} in {os.path.join(CALC_SCRIPT_MODULE_DIR, CALC_SCRIPT_FILE_NAME)}")
    else:
        print("No best value found, all evaluations may have failed or produced similar errors.")
    print("-------------------------------------")
    return best_value_for_param, min_avg_error

# --- Main Execution ---
if __name__ == "__main__":
    # Load test cases first as it's common to all modes
    try:
        with open(PUBLIC_CASES_JSON_PATH, 'r') as f:
            all_test_cases = json.load(f)
        print(f"Loaded {len(all_test_cases)} test cases from {PUBLIC_CASES_JSON_PATH}.")
    except FileNotFoundError:
        print(f"Error: Test cases file not found at {PUBLIC_CASES_JSON_PATH}")
        sys.exit(1)
    except json.JSONDecodeError:
        print(f"Error: Could not decode JSON from {PUBLIC_CASES_JSON_PATH}")
        sys.exit(1)

    current_default_params = deepcopy(DEFAULT_PARAMS)

    if len(sys.argv) > 1 and sys.argv[1].lower() == 'random':
        if len(sys.argv) != 3:
            print("Usage for random search: python tune_parameters.py random <num_trials>")
            print("Example: python tune_parameters.py random 100")
            sys.exit(1)
        try:
            num_trials_for_random_search = int(sys.argv[2])
            if num_trials_for_random_search <= 0:
                raise ValueError("Number of trials must be positive.")
        except ValueError as e:
            print(f"Error: Invalid number of trials. {e}")
            sys.exit(1)
        # random_search_parameters handles its own printing of results
        random_search_parameters(num_trials_for_random_search, all_test_cases, current_default_params)
    
    elif len(sys.argv) >= 3:
        parameter_name_to_tune = sys.argv[1]
        values_to_test_str = sys.argv[2:]
        
        if parameter_name_to_tune not in DEFAULT_PARAMS:
            print(f"Error: Parameter '{parameter_name_to_tune}' not found in DEFAULT_PARAMS.")
            print(f"Available parameters: {list(DEFAULT_PARAMS.keys())}")
            sys.exit(1)

        # Determine parameter type for conversion
        param_info = PARAMETER_RANGES.get(parameter_name_to_tune)
        param_type_for_conversion = 'float' # Default type
        if param_info and len(param_info) == 3: # Check if param_info is valid
            param_type_for_conversion = param_info[2]
        
        try:
            if param_type_for_conversion == 'int':
                param_values_to_test = [int(v) for v in values_to_test_str]
            else: # Default to float for safety and for 'float' type
                param_values_to_test = [float(v) for v in values_to_test_str]
        except ValueError:
            print(f"Error: Could not convert values for {parameter_name_to_tune} to expected type ({param_type_for_conversion}).")
            sys.exit(1)
        
        # tune_single_parameter handles its own printing of results
        tune_single_parameter(parameter_name_to_tune, param_values_to_test, all_test_cases, current_default_params)
    
    else:
        print("\nUsage:")
        print("  For random search: python tune_parameters.py random <num_trials>")
        print("  For single parameter tuning: python tune_parameters.py <parameter_name> <value1> <value2> ...")
        print("\nAvailable parameters for single tuning (from DEFAULT_PARAMS):")
        for p_name in DEFAULT_PARAMS.keys():
            print(f"  - {p_name}")
        sys.exit(1)

