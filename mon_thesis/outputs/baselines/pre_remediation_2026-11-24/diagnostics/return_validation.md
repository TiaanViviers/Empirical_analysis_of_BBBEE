# Return validation

Compared 980380 computed returns; discrepancies: 0
Formula: current / previous - 1; finite positive endpoints and adjacent supplied-calendar sessions required.
No interpolation, filling, price adjustment, clipping or conversion to total returns.
2024-01-02 is missing in J203; both 2 and 3 January returns are NA.
Full placeholder panel used for calculation; only non-placeholder rows stored in derived returns.
Missing derived rows never imply zero returns; session IDs retain adjacency semantics.
