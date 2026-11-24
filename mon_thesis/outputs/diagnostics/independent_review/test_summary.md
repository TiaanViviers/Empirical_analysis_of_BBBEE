# Executed automated tests

Test cases: 18
Expectations passed: 331
Failed expectations: 0
Errors: 0
Skipped cases: 0

Executed in a clean Rscript session. Includes real-input integration, independent lm/CAR checks, synthetic shocks, synchronous dependence, null calibration and block-gap handling.

| file | test | nb | passed | failed | skipped | error |
| --- | --- | --- | --- | --- | --- | --- |
| test-car-caar.R | known shock gives correct AR, CAR, CAAR and spread | 6 | 6 | 0 | FALSE | FALSE |
| test-data-integrity.R | many-to-one joins fail rather than multiply prices | 2 | 2 | 0 | FALSE | FALSE |
| test-data-integrity.R | event-specific classifications retain unknowns and historical attributes | 4 | 4 | 0 | FALSE | FALSE |
| test-event-windows.R | trading windows use supplied sessions and correct inclusive lengths | 6 | 6 | 0 | FALSE | FALSE |
| test-inference.R | blocks never bridge missing sessions and are deterministic | 6 | 6 | 0 | FALSE | FALSE |
| test-inference.R | a single admissible block start is sampled as a position | 4 | 4 | 0 | FALSE | FALSE |
| test-inference.R | synchronous common shocks cancel exactly in a spread | 2 | 2 | 0 | FALSE | FALSE |
| test-inference.R | bootstrap OLS prediction error agrees with explicit refitting | 1 | 1 | 0 | FALSE | FALSE |
| test-inference.R | five-session bootstrap preserves configured estimation-to-event gaps | 9 | 9 | 0 | FALSE | FALSE |
| test-inference.R | null synthetic simulations have a plausible rejection rate | 1 | 1 | 0 | FALSE | FALSE |
| test-inference.R | moving blocks retain persistent time-series variability | 1 | 1 | 0 | FALSE | FALSE |
| test-integration.R | real 2017 models and CARs independently reconcile to outputs | 22 | 22 | 0 | FALSE | FALSE |
| test-market-models.R | OLS recovers known parameters and agrees with independent lm | 5 | 5 | 0 | FALSE | FALSE |
| test-output-consistency.R | published CSV mean CAR and inference estimates agree with derived CARs | 242 | 242 | 0 | FALSE | FALSE |
| test-output-consistency.R | percentage headline export creates and refreshes its own output | 9 | 9 | 0 | FALSE | FALSE |
| test-returns.R | adjacent returns distinguish missing, zero, stale and extreme values | 5 | 5 | 0 | FALSE | FALSE |
| test-returns.R | missing J203 session does not yield a multi-day daily return | 2 | 2 | 0 | FALSE | FALSE |
| test-sample-selection.R | actual sample screens use only pre-event historical information | 4 | 4 | 0 | FALSE | FALSE |
