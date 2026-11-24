# Return validation

Compared 980380 computed returns; discrepancies: 0
Formula: current / previous - 1; finite positive endpoints and adjacent supplied-calendar sessions required.
Raw source diagnostic returns are reconciled before any analytical conversion correction. No filling or clipping.
Analytical returns correct only verified security-unit conversions in the versioned ledger; see corporate_action_application.csv.
These are unit-consistent price returns, not dividend-reinvested total shareholder returns. Cash actions with unresolved units are not applied.
2024-01-02 is missing in J203; both 2 and 3 January returns are NA.
Full placeholder panel used for calculation; only non-placeholder rows stored in derived returns.
Missing derived rows never imply zero returns; session IDs retain adjacency semantics.
