# Data-quality and identity review

Extreme-return counts and full-year distributions are recorded in return_quality_summary.csv. event_sample_extreme_returns.csv isolates every flagged change among fitted event samples, preserving date, security, volume and historical industry.
influential_primary_cars.csv ranks the 20 largest absolute [0,+1] CARs per event. largest_null_portfolio_shocks.csv identifies pre-event common dates that dominate portfolio variability. Neither list establishes corporate actions or data error.
The source-wide audit retains every >30% valid price ratio. No source movement is adjusted or deleted in the baseline. Severe deletion sensitivity is only diagnostic; source corporate-action records are still needed.

## Exposure contamination requiring review

The supplied exact-label proxy places Iron & Steel instruments in non-mining, including KIO:XJSE:EQU. Such categories can contain mineral-related firms and weaken a legal-treatment interpretation. mineral_value_chain_controls.csv lists affected sample members. A broader mineral-value-chain sensitivity reassigns these labels provisionally, without asserting direct Mining Charter applicability.

| event_id | instrument_id | historical_security_name | nature_of_business_raw |
| --- | --- | --- | --- |
| mining_charter_2017 | ACL:XJSE:EQU | ArcelorMittal SA Limited | Iron & Steel |
| mining_charter_2017 | KIO:XJSE:EQU | Kumba Iron Ore Ltd | Iron & Steel |
| mining_charter_2018 | ACL:XJSE:EQU | ArcelorMittal SA Limited | Iron & Steel |
| mining_charter_2018 | KIO:XJSE:EQU | Kumba Iron Ore Ltd | Iron & Steel |
| ee_draft_2023 | ACL:XJSE:EQU | ArcelorMittal SA Limited | Iron & Steel |
| ee_draft_2023 | KIO:XJSE:EQU | Kumba Iron Ore Ltd | Iron & Steel |
| ee_final_2025 | ACL:XJSE:EQU | ArcelorMittal SA Limited | Iron & Steel |
| ee_final_2025 | KIO:XJSE:EQU | Kumba Iron Ore Ltd | Iron & Steel |
| bbbee_draft_2026 | ACL:XJSE:EQU | ArcelorMittal SA Limited | Iron & Steel |
| bbbee_draft_2026 | KIO:XJSE:EQU | Kumba Iron Ore Ltd | Iron & Steel |

## Multiple-security evidence

Repeated historical source-label groups: 0 ; repeated valid contemporary ISIN groups: 0
Repeated labels/current ISINs are review candidates only, not confirmed historical issuer links. No current listing status enters eligibility. Verified historical issuer consolidation remains unsupported.

No supported estimates.

No supported estimates.
