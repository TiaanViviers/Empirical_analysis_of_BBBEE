# Return measurement and corporate-action ledger

The preferred analytical series is **security-unit-consistent price returns**.
It is not a verified total shareholder return series. Ordinary dividends and
capital distributions are not selectively added to a price-only panel.
Unresolved capital actions remain limitations and receive labelled sensitivity
analysis. This choice preserves a consistent interpretation rather than mixing
cash-inclusive returns for a few firms with unadjusted price changes elsewhere.

## Raw and analytical fields

For adjacent supplied-calendar sessions with finite positive closes,
`return_raw = close_raw[t] / close_raw[t-1] - 1`. No missing session or invalid
close is bridged. `close_raw`, volume, source flags and
`diagnostic_price_return` remain untouched. All 980,380 valid source ratios are
checked before analytical corrections.

`return` is the analytical series used by fitting, AR, CAR and bootstrap donors.
For an approved unit conversion only,
`return = (1 + return_raw) / price_multiplier - 1` on its effective date.
Subsequent ratios are already in the new units. There is no need to overwrite
historical prices. `adjustment_id` and `adjustment_factor` identify the operation;
`extreme_raw` and `extreme` distinguish raw and analytical >30% movements.
Turning off verified conversions restores `return_raw` as a labelled measurement
comparison. Reapplying the correction is idempotent because it always starts
from the retained raw ratio.

## Versioned evidence

`research/corporate_actions_v1.csv` records the ledger version, action ID,
instrument, effective date, type, multiplier or cash amount/currency, quote-unit
status, verification/application status, primary evidence, review date and
unresolved questions. A pending factor is not an instruction to apply it.
`outputs/diagnostics/corporate_action_application.csv` records what each run
actually applied and the original/revised ratios.

The approved Reinet conversion is supported by the
[FTSE/JSE notice dated 22 November 2017](https://clientportal.jse.co.za/Content/ICANoticeItems/FTSE-JSE-Africa/20171129%20Reinet%20Conversion%20of%20Depositary%20Receipts%20Informative%20Notice.pdf).
Ten receipts became one share on 29 November: the raw 3,000→29,585 ratio is
+886.1667%, while `29585/(3000*10)-1` is −1.3833%. This factor is unit-free.

MTNZF's [issuer announcement](https://senspdf.jse.co.za/documents/SENS_20250715_S507582.pdf)
confirms a R20 capital distribution and 23 July 2025 ex-date. The vendor's quote
units and complete unwind return treatment have not been certified. The
cents-based cash-inclusive calculation in the independent review is a
diagnostic, not a baseline correction. Aveng's
[rights-offer announcement](https://senspdf.jse.co.za/documents/SENS_20180605_S400508.pdf)
confirms the 13 June 2018 ex-entitlement date; a provider-consistent rights-return
adjustment remains unresolved. Both receive a targeted whole-security exclusion
sensitivity when their action falls in the fitted/event horizon.

The ledger also keeps unresolved influential jumps without guessed factors.
Steinhoff's December 2017 collapse is classified as news, rather than a split,
using the [FSCA tribunal record](https://www.fsca.co.za/Enforcement-Matters/Publications%20and%20Documents/Decision%20-%20Markus%20J%20Jooste%20and%20Ocsan%20Investment%20Enterprises%20%28Pty%29%20Ltd%20and%20FSCA.pdf).
A large ratio alone is never proof of an adjustment error.

## Benchmark convention and unresolved work

JSE identifies [J203 as All Share](https://www.jse.co.za/all-share-j203) and
separately identifies [J203T as All Share Total Return](https://www.jse.co.za/jse/instruments/3416).
This supports the intended price-index comparison; it does not independently
certify how IRESS exported the exact historical series. Provider-level equity
adjustment, special-distribution and benchmark conventions remain partially
unverified. The ledger is a targeted correction pass, not a comprehensive
corporate-action history.

Code: `R/01_construct_returns.R`, `R/01a_corporate_actions.R`. Tests cover the
conversion, raw-field preservation, reversibility, idempotence and refusal to
apply unverified cash/factor adjustments. The independent NumPy verifier reads
source observations and the ledger separately before refitting all models.
