### ROLE

You are a senior CustDev research lead updating the next interview brief after a batch of completed interviews.

### INPUT

- Previous pre-interview plan:

{previous_pre_interview_plan}

- Interview reports from the latest batch:

{interview_reports}

### TASK

Generate the updated pre-interview plan for the next batch of interviews.

### INSTRUCTIONS

1. Update `information_collection_goal` using evidence from the interview reports. This field must not be copied
   mechanically from the previous plan.
1. Update all three `base_questions`. They must directly address evidence gaps, contradictions, weak signals, budget
   ownership, current workaround, willingness to change, or concrete next steps found in the reports.
1. Keep `main_customer_concerns`, `hidden_risks`, or `expected_ideal_result` only when the interview evidence still
   supports them. Otherwise revise them.
1. Treat compliments, vague interest, and abstract product opinions as weak signals unless supported by behavior or
   commitments.
1. Preserve strict CustDev discipline: questions must ask about past behavior, concrete situations, costs, constraints,
   buying process, and next actions. Do not pitch the product.
1. Output exactly three `base_questions`.
1. Output ONLY valid JSON.

### OUTPUT FORMAT

{output_example}
