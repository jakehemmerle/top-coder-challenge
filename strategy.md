# Solution Strategies for Black Box Legacy Reimbursement System

This document outlines two primary strategies for reverse-engineering the legacy reimbursement system, along with detailed actionable steps for each. It concludes with a recommended approach.

## Strategy 1: Interview-Driven Incremental Rule Building

**Core Idea:** This strategy prioritizes the qualitative information from `INTERVIEWS.md` and `PRD.md`. Employee interviews are treated as a primary source of hypotheses about the system's rules, including its quirks and bugs. Each hypothesized rule is implemented incrementally, and `public_cases.json` is used to validate, refine, and find the precise parameters for these rules.

**Detailed Actionable Steps:**

**Step 1.1: Rule Extraction & Prioritization**

* **Action 1.1.1:** Thoroughly read and digest `INTERVIEWS.md` (Marcus from Sales, Lisa from Accounting) and relevant sections of `PRD.md` focusing on system behavior and suspected logic.
* **Action 1.1.2:** Create a structured list (e.g., in a separate text file, spreadsheet, or within this document) of all potential rules, rates, thresholds, bonuses, penalties, and quirks mentioned. For each item, note:
  * The specific detail (e.g., "5-day trip bonus," "mileage tiered around 100 miles," "receipts ending in .49 or .99 get rounded up").
  * The source (Marcus, Lisa, PRD).
  * Any specific values mentioned (e.g., "$100/day base per diem," "58 cents per mile for first tier").
  * Confidence/clarity level of the hint.
* **Action 1.1.3:** Prioritize this list. High priority items are those that are:
  * Mentioned by multiple sources or with high confidence.
  * Seem to explain fundamental parts of the calculation (e.g., base per diem, primary mileage rate).
  * Are described with specific, testable parameters.

**Step 1.2: Setup Initial Development Environment & Baseline Implementation**

* **Action 1.2.1:** Copy `run.sh.template` to `run.sh` in your working directory.
* **Action 1.2.2:** Choose an implementation language. Python 3 is highly recommended due to its readability, data handling capabilities, and standard library (fitting the "no external dependencies" rule if only standard modules are used). Create the main logic file (e.g., `calculate_reimbursement.py`).
* **Action 1.2.3:** Modify `run.sh` to execute your chosen script. For Python, this would be something like: `python3 calculate_reimbursement.py "$1" "$2" "$3"`.
* **Action 1.2.4:** Inside your script (e.g., `calculate_reimbursement.py`):
  * Parse the three input arguments: `trip_duration_days` (int), `miles_traveled` (int), `total_receipts_amount` (float).
  * Implement the most basic, fundamental rules as a starting point. For example:
    * `per_diem_reimbursement = trip_duration_days * 100.0` (based on Lisa's $100/day hint).
    * `mileage_reimbursement = miles_traveled * 0.58` (based on Lisa's 58cpm hint for the first tier).
    * `receipt_reimbursement = total_receipts_amount` (simple pass-through initially).
    * `total_reimbursement = per_diem_reimbursement + mileage_reimbursement + receipt_reimbursement`.
* **Action 1.2.5:** Ensure your script prints only a single numeric value (the `total_reimbursement`), formatted to two decimal places (e.g., using `print(f"{total_reimbursement:.2f}")` in Python).
* **Action 1.2.6:** Run `./eval.sh` to get an initial baseline score. Note the `exact_matches`, `average_error`, and the list of high-error cases. This baseline will be your reference for improvement.

**Step 1.3: Iterative Rule Layering & Parameter Tuning**

* **Action 1.3.1:** Select the next highest-priority rule from your list (from Action 1.1.3) that has not yet been implemented.
* **Action 1.3.2: Hypothesize Parameters & Logic:** Based on the interview hints, define the precise logic for this rule and make initial guesses for any unknown parameters (e.g., for a "5-day trip bonus," the logic is `if trip_duration_days == 5: add bonus_amount`. Initial guess: `bonus_amount = 50.0`).
* **Action 1.3.3: Implement Rule:** Add the conditional logic and calculations for this new rule into your script.
* **Action 1.3.4: Focused Data Analysis (using `public_cases.json`):**
  * To validate and tune the rule, filter `public_cases.json` to isolate cases specifically relevant to it. For example, if implementing the 5-day trip bonus, analyze only cases where `trip_duration_days == 5`.
  * For this subset, compare the `expected_output` with the output your script *would* produce *without* the new rule (or with its initial guessed parameters). The difference should reveal the effect of the rule (e.g., the actual bonus amount).
  * Use this analysis to refine the parameters of your rule (e.g., determine the exact bonus amount, the precise mileage rate for a tier, the threshold for a penalty).
* **Action 1.3.5: Tune Parameters in Script:** Update the parameters in your script based on the findings from Action 1.3.4.
* **Action 1.3.6: Test (Full Evaluation):** Run `./eval.sh` again.
* **Action 1.3.7: Analyze Impact:** Compare the new score and error metrics to the previous run.
  * Did `exact_matches` increase significantly?
  * Did `average_error` decrease?
  * Did the rule negatively affect cases it wasn't supposed to, or interact poorly with existing rules?
* **Action 1.3.8: Decide and Document:**
  * If the rule clearly improves the score and makes logical sense, keep it.
  * If it makes things worse or has no clear benefit, re-evaluate its interpretation, parameters, or its interaction with other rules. Consider temporarily disabling it or refining its conditions.
  * Document the implemented rule, its parameters, and the justification/evidence from data or interviews.
* **Action 1.3.9:** Repeat Actions 1.3.1 to 1.3.8 for the next rule on your prioritized list.

**Step 1.4: Address Complex Interactions & Quirks**

* **Action 1.4.1:** Once several basic rules are in place and tuned, review your rule list and interview notes for potential interactions between rules (e.g., Lisa: "people who keep their expenses modest on long trips seem to do better on mileage reimbursement").
* **Action 1.4.2:** Formulate hypotheses for how these interactions manifest (e.g., mileage rate slightly increases if `total_receipts_amount / trip_duration_days` is below a certain threshold on trips longer than X days).
* **Action 1.4.3:** Implement these interaction rules. This will likely involve more complex conditional logic that modifies parameters or results of existing rule calculations.
* **Action 1.4.4:** Test thoroughly using `./eval.sh` and focused data analysis on relevant subsets of `public_cases.json` to validate the interaction.
* **Action 1.4.5:** Specifically investigate and implement "quirks" like the receipt rounding (Lisa: "If your receipts end in 49 or 99 cents, you often get a little extra money").
  * Filter `public_cases.json` for cases where `total_receipts_amount` ends in `.49` or `.99`.
  * Compare `expected_output` with your script's prediction for these cases. If there's a consistent small positive difference, implement a small upward adjustment for these specific receipt endings.

**Step 1.5: Continuous Error Analysis & Refinement**

* **Action 1.5.1:** After each significant change or a batch of related rule implementations, run `./eval.sh`.
* **Action 1.5.2:** Systematically examine the top 5 (or more) high-error cases reported by `eval.sh`.
* **Action 1.5.3:** For each high-error case:
  * Note the input values: `trip_duration_days`, `miles_traveled`, `total_receipts_amount`.
  * Manually trace the logic of your current script with these inputs to understand what it *should* output according to its rules.
  * Compare your script's actual output, your manually traced output, and the `expected_output` from `public_cases.json`.
* **Action 1.5.4:** Identify the likely source of the discrepancy: Is it an incorrect parameter value? A missing rule that applies to this case? A flawed interaction between existing rules? An edge case not yet considered?
* **Action 1.5.5:** Revisit your rule list and `INTERVIEWS.md` for any overlooked clues that might explain the errors in these specific cases.
* **Action 1.5.6:** Make targeted adjustments to your script (modify parameters, add/refine rule conditions, implement new small rules) to address these specific errors, then re-evaluate to ensure the fix doesn't break other cases.

**Step 1.6: Iteration and Finalization**

* **Action 1.6.1:** Continue the cycle of implementing rules (Step 1.3), addressing interactions/quirks (Step 1.4), and analyzing errors (Step 1.5) until the score from `./eval.sh` no longer shows significant improvement, or all credible hints from interviews have been investigated.
* **Action 1.6.2:** Perform a final review of your script for logical consistency, clarity, and any potential simplifications that don't sacrifice accuracy.
* **Action 1.6.3:** Double-check that your solution adheres to all constraints mentioned in `README.md` (takes 3 parameters, outputs a single number, runs under 5 seconds, no external dependencies beyond standard language capabilities).
* **Action 1.6.4:** Run `./generate_results.sh` to produce your `private_results.txt` for submission.

---

## Strategy 2: Data-Driven Segmentation & Localized Modeling

**Core Idea:** This strategy starts with a quantitative analysis of `public_cases.json` to identify distinct segments or clusters of data that appear to follow different calculation patterns. Simpler, localized models are then developed for these segments, using the interviews for guidance on what rules might apply within each segment.

**Detailed Actionable Steps:**

**Step 2.1: Exploratory Data Analysis (EDA) & Segmentation**

* **Action 2.1.1:** Load `public_cases.json` into a data analysis environment (e.g., Python with pandas, numpy, matplotlib, seaborn). If using Python for the main solution, this can be a separate Jupyter notebook or script.
* **Action 2.1.2:** Generate descriptive statistics (mean, median, min, max, stddev) for `trip_duration_days`, `miles_traveled`, `total_receipts_amount`, and `expected_output`.
* **Action 2.1.3:** Create visualizations to understand distributions and relationships:
  * Histograms or density plots for each input variable and `expected_output`.
  * Scatter plots: `expected_output` vs. `trip_duration_days`, `expected_output` vs. `miles_traveled`, `expected_output` vs. `total_receipts_amount`.
  * Consider plotting derived features that might reveal underlying rates, e.g.:
    * `per_diem_approx = expected_output / trip_duration_days` (plot vs. `trip_duration_days`).
    * `mileage_reimbursement_approx = expected_output - (trip_duration_days * assumed_daily_rate)` (plot `mileage_reimbursement_approx / miles_traveled` vs. `miles_traveled`).
* **Action 2.1.4:** Look for visual evidence of:
  * Clear breakpoints where trends change.
  * Distinct clusters of data points.
  * Non-linear relationships that might simplify within specific ranges.
* **Action 2.1.5:** Based on these observations (and potentially guided by strong hints from interviews, like the 5-day trip specialness), define initial segments. Examples:
  * Segment A: `trip_duration_days == 5`
  * Segment B: `trip_duration_days < 3` AND `miles_traveled < 100`
  * Segment C: `miles_traveled > 500`
* **Action 2.1.6 (Optional Advanced):** Apply clustering algorithms (e.g., K-Means on scaled input features) to see if data-driven clusters emerge. Evaluate if these clusters are meaningful and interpretable.

**Step 2.2: Hypothesis Generation per Segment (Interview-Guided)**

* **Action 2.2.1:** For each segment identified in Step 2.1, analyze the characteristics of the data points within it (e.g., average values, ranges of inputs).
* **Action 2.2.2:** Review `INTERVIEWS.md` specifically looking for rules, comments, or theories that seem most applicable to the characteristics of the current segment. (e.g., for a segment of "long trips, high mileage," Marcus's comments about 600 vs. 800-mile trips and Lisa's "mileage curve" would be relevant).
* **Action 2.2.3:** Formulate hypotheses about the dominant calculation logic or key rules that apply primarily *within* this segment.

**Step 2.3: Localized Model Fitting**

* **Action 2.3.1:** For each segment, extract the subset of data from `public_cases.json` that belongs to it.
* **Action 2.3.2:** Attempt to fit a relatively simple model to this subset to explain its `expected_output` values:
  * If relationships appear linear within the segment, try fitting a simple linear regression model (`expected_output ~ c0 + c1*days + c2*miles + c3*receipts`) to find segment-specific coefficients.
  * If specific rates or formulas are suspected from interview hints relevant to this segment, try to derive/estimate them using the segment's data.
  * Implement a small, targeted set of if-else rules based on interview hints that strongly map to this segment's characteristics.
* **Action 2.3.3:** Evaluate the performance of this localized model *within its own segment* (e.g., calculate R-squared, Mean Absolute Error for that subset).

**Step 2.4: Combine Segment Models into a Unified Script**

* **Action 2.4.1:** In your main reimbursement script (e.g., `calculate_reimbursement.py`):
  * Implement logic at the beginning to determine which segment an incoming test case (days, miles, receipts) belongs to. This will be a series of `if/elif/else` statements based on the segmentation criteria from Action 2.1.5.
* **Action 2.4.2:** Once the segment is identified, apply the specific localized model, formulas, or rules developed for that segment in Step 2.3.

**Step 2.5: Global Refinement & Quirk Integration**

* **Action 2.5.1:** Test the full, combined model (with segment-switching logic) using `./eval.sh`.
* **Action 2.5.2:** Analyze overall errors. Pay particular attention to:
  * Cases that fall near the boundaries of your defined segments. Are they being misclassified, or is the transition in logic too abrupt?
  * Systematic errors that appear across multiple segments. This might indicate a global rule (e.g., an overall cap on reimbursement) or a universal quirk is missing.
* **Action 2.5.3:** Revisit `INTERVIEWS.md` for global quirks (like the receipt rounding for .49/.99 cents) and implement them. These might be applied as a final adjustment step after the segment-specific calculation, or as an override condition.
* **Action 2.5.4:** Iteratively refine segment definitions (adjust boundaries, merge/split segments) and the models/rules within each segment based on error analysis.

**Step 2.6: Iteration and Finalization**

* **Action 2.6.1:** Continue the cycle of refining segments (Step 2.1/2.5), tuning localized models (Step 2.3), and integrating global rules/quirks (Step 2.5) until the score from `./eval.sh` no longer significantly improves.
* **Action 2.6.2:** Perform a final review of the script for logical consistency and clarity, especially the segment-switching logic.
* **Action 2.6.3:** Ensure the solution meets all constraints (performance, no external dependencies).
* **Action 2.6.4:** Run `./generate_results.sh` to produce `private_results.txt`.

---

## Recommended Strategy & Justification

**Recommendation:** Primarily pursue **Strategy 1: Interview-Driven Incremental Rule Building**, while strategically incorporating data analysis techniques from Strategy 2.

**Justification:**

1. **Nature of the Problem:** The task is to reverse-engineer a system likely built with human-defined rules, exceptions, and accumulated modifications over time. A rule-based approach (Strategy 1) directly attempts to reconstruct this type of logic. The employee interviews are rich with clues about these original rules.
2. **Richness of Qualitative Data:** `INTERVIEWS.md` provides numerous specific, testable hypotheses (e.g., "5-day bonus," "mileage tiered at 100 miles / 58cpm," "receipt rounding for .49/.99"). Strategy 1 leverages this direct information as its foundation.
3. **Interpretability and Debuggability:** Building the model rule by rule makes it more interpretable. If adding or modifying a rule negatively impacts the score, that specific piece of logic can be isolated, examined, and corrected more easily than debugging a complex, multi-segment model.
4. **Explicitly Handling Quirks and Bugs:** The PRD mandates the replication of bugs. Strategy 1 allows for the explicit coding and testing of suspected bugs mentioned in interviews (like receipt rounding or specific inconsistent bonuses). These might be averaged out or missed by a purely data-segmented approach.
5. **Risk of Overfitting with Purely Data-Driven Segmentation (Strategy 2):** Relying heavily on segmenting `public_cases.json` and fitting models to those segments carries a risk of overfitting to the specific characteristics of those 1,000 cases. Rules derived from interview narratives about general system behavior are more likely to generalize to the unseen `private_cases.json`.
6. **Manageable Complexity:** Strategy 1 allows for a more gradual and controlled increase in model complexity. One can start with a very simple model and incrementally add and test rules, observing the impact at each stage.

**Incorporating Strengths from Strategy 2 into Strategy 1:**

While Strategy 1 is the primary path, the data analysis techniques from Strategy 2 are crucial supporting elements:

* **Parameter Tuning:** When a rule is hypothesized from an interview (e.g., "tiered mileage"), EDA on `public_cases.json` (as in Action 1.3.4) is essential to find the *optimal* parameters (e.g., the exact mileage thresholds, the specific rates for each tier, the precise bonus amounts).
* **Validating Hypotheses:** Before implementing a complex rule derived from an interview, `public_cases.json` can be quickly queried to see if there's data supporting the general pattern.
* **Discovering Missing Rules or Refining Conditions:** If, after implementing many interview-based rules, significant error patterns remain (identified in Step 1.5), the EDA techniques of Strategy 2 (analyzing residuals, looking for unexplained clusters or trends in high-error cases) can help identify new rules, refine the conditions of existing rules, or uncover interactions not explicitly mentioned in interviews.

By leading with interview insights to structure the model (Strategy 1) and using rigorous data analysis on `public_cases.json` (techniques from Strategy 2) at every step for validation, tuning, and discovery, we can build a robust and accurate replica of the legacy system.
