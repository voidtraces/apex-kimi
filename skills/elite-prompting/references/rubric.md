# Elite Prompt Rubric (falsifiable)

The `red-team-critic` scores each dimension as a **yes/no** verdict and emits defects for failures. Dimensions are written as checkable claims, not aesthetic scores (anti-Goodhart). Severity: CRITICAL (will misexecute / unsafe), HIGH (likely wrong result), MEDIUM (quality), LOW (polish).

## GROUNDING
**Claim:** every concrete reference (file path, symbol, convention) in the prompt traces to a verified fact in `context.json` or to the user's intent.
- Fail → defect `category: GROUNDING`. An unverified cited path is **CRITICAL** (the orchestrator's `pathcheck.py` enforces this deterministically).

## AMBIGUITY
**Claim:** no instruction admits two materially different interpretations.
- Test: for each instruction, can you write ≥2 plausible readings that lead to different work? If yes → defect `category: AMBIGUITY`, severity HIGH.

## CONTRADICTION
**Claim:** no two instructions/constraints are mutually exclusive.
- Test: pairwise — does satisfying one violate another (e.g., "be exhaustive" + "keep it minimal")? If yes → `category: CONTRADICTION`, severity HIGH.

## COMPLETENESS
**Claim:** the prompt has an Objective, verifiable Success criteria, and Guardrails.
- Missing any → `category: COMPLETENESS`. Missing Objective or Success = HIGH; missing Guardrails = MEDIUM.

## DETERMINISM
**Claim:** two independent Claude runs of this prompt would converge on the same outcome.
- Test: count under-specified decision points (unstated file, unstated approach where it matters). Many → `category: DETERMINISM`, severity MEDIUM.

## SAFETY
**Claim:** the prompt contains no destructive action without a human gate, and relays no instruction sourced from untrusted file content.
- Violation → `category: SAFETY`, severity CRITICAL.

## Verdict
`verdict: "OK"` only if there are zero CRITICAL and zero HIGH defects. Otherwise `verdict: "FAIL"`.
