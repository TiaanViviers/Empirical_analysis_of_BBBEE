# Information timing and market conditions

Registered official publication dates remain the baseline. Earlier dates are distinct information events, never selected by significance.
The 2017 [0,+1] sessions are 15 and 19 June. The 2018 21 September window ends 25 September after the holiday/weekend.
The 2018 baseline measures incremental gazette-window relative performance, not the complete information sequence. Approval was public by the presidential stimulus statement of 21 September.
The 2023 diplomatic episode, 2025 tariff-related outlook news and 2026 monetary/global-market developments prevent isolated causal attribution. Dated overlap alone does not establish an intraday causal effect.

| event_id | information_date | information_type | public_information_status | source_url | interpretation | first_disclosure_verified |
| --- | --- | --- | --- | --- | --- | --- |
| mining_charter_2017 | 2017-06-15 | release_and_gazette | public release date verified | https://www.gov.za/speeches/minister-mosebenzi-zwane-occasion-release-mining-charter-15-jun-2017-0000 | Baseline measures release-date and next-session conditional valuation changes; earlier approval/consultation may be anticipated. | FALSE |
| mining_charter_2017 | 2017-06-16 | public_holiday | calendar non-session | https://www.gov.za/about-sa/public-holidays | Youth Day and weekend intervene; [0,+1] uses 15 and 19 June. | FALSE |
| mining_charter_2018 | 2018-09-19 | cabinet_meeting | meeting date only; first public availability not verified | https://www.gov.za/news/media-advisories/media-briefings/minister-gwede-mantashe-briefs-media-gazetting-mining-charter | Reference-date sensitivity; not asserted to be first disclosure. | FALSE |
| mining_charter_2018 | 2018-09-21 | presidential_stimulus_approval | public information by this date | https://www.thepresidency.gov.za/statement-president-cyril-ramaphosa-economic-stimulus-and-recovery-plan | Distinct approval/stimulus information event with other macro measures; [0,+1] ends 25 September. | FALSE |
| mining_charter_2018 | 2018-09-26 | ministerial_advisory | public advisory date verified | https://www.gov.za/news/media-advisories/media-briefings/minister-gwede-mantashe-briefs-media-gazetting-mining-charter | Sensitivity overlaps 27 September release; not an unaffected control day. | FALSE |
| mining_charter_2018 | 2018-09-27 | gazette_and_release | official baseline publication date | https://www.gov.za/news/media-statements/minister-gwede-mantashe-release-mining-charter-2018-27-sep-2018 | Incremental gazette-window response conditional on prior information; not entire Charter information sequence. | FALSE |
| ee_draft_2023 | 2023-05-12 | draft_targets_gazette | publication date verified | https://www.gov.za/xh/documents/notices?order=field_gcisdoc_document_date&page=235&sort=desc | Aggregate abnormal price response around draft-target publication; no unaffected group or measured target gap. | FALSE |
| ee_final_2025 | 2025-04-15 | final_targets_gazette | gazette date verified; prior upload remains unresolved | https://www.gov.za/sites/default/files/gcis_document/202504/52514gon6124.pdf | Aggregate final-target gazette-window response; signature/upload timing is not first disclosure proof. | FALSE |
| bbbee_draft_2026 | 2026-01-29 | draft_code_bundle | gazette date verified; bundle and first upload incomplete | https://www.gov.za/sites/default/files/gcis_document/202601/54032gon3743_0.pdf | Aggregate market-model relative performance around multiple draft notices, not an isolated causal B-BBEE effect. | FALSE |

| event_id | news_date | news_type | source_url | verified_information | timing_caveat | causal_attribution_status |
| --- | --- | --- | --- | --- | --- | --- |
| mining_charter_2018 | 2018-09-21 | domestic_stimulus_and_mining_approval | https://www.thepresidency.gov.za/statement-president-cyril-ramaphosa-economic-stimulus-and-recovery-plan | President discusses revised Charter approval within a broader economic package. | Date verified; first disclosure hour unresolved. | overlap only; causal contribution not estimated |
| ee_draft_2023 | 2023-05-11 | US_South_Africa_diplomatic_news | https://www.parliament.gov.za/storage/app/media/Docs/exe_rq_na/6df0fbe6-ba5b-471a-be11-cccb387ed193.pdf | Ministerial reply documents ambassador allegations on 11 May and official response on 12 May. | Overlaps anticipation and release window. | overlap only; causal contribution not estimated |
| ee_draft_2023 | 2023-05-12 | government_diplomatic_response | https://www.parliament.gov.za/storage/app/media/Docs/exe_rq_na/6df0fbe6-ba5b-471a-be11-cccb387ed193.pdf | Official response to ambassador allegations on the draft-target date. | Intraday market response not isolated. | overlap only; causal contribution not estimated |
| ee_final_2025 | 2025-04-14 | tariff_uncertainty_context | https://www.federalreserve.gov/newsevents/speech/files/waller20250414a.pdf | Federal Reserve speech discusses tariff changes and policy uncertainty. | Context before baseline; not a quantified local-market shock. | context; no causal estimate |
| ee_final_2025 | 2025-04-16 | Federal_Reserve_tariff_outlook | https://www.federalreserve.gov/newsevents/speech/powell20250416a.htm | Powell discusses tariffs and uncertain economic effects. | US speech time relative to JSE close must be verified before calling it within-session news. | dated overlap; intraday attribution unresolved |
| bbbee_draft_2026 | 2026-01-29 | SARB_MPC | https://www.reservebank.co.za/en/home/publications/publication-detail-pages/statements/monetary-policy-statements/2026/january | MPC held the policy rate at 6.75 percent with a divided vote. | Overlaps draft-code publication day. | overlap only; causal contribution not estimated |
| bbbee_draft_2026 | 2026-01-30 | US_Fed_chair_nomination | https://www.whitehouse.gov/releases/2026/01/wide-acclaim-for-president-trumps-nomination-of-kevin-warsh-as-fed-chair/ | White House announces Kevin Warsh nomination. | Pool report records announcement before 09:13 US Eastern; within South African trading day. | overlap only; causal contribution not estimated |
| bbbee_draft_2026 | 2026-01-30 | precious_metals_market_conditions | https://www.gold.org/goldhub/research/gold-market-commentary-january-2026 | World Gold Council retrospectively records large intraday swings on final two January trading days. | Retrospective context; no external commodity-return series imported. | context; no causal estimate |

Daily raw, unit-consistent, predicted and abnormal returns are in primary_daily_decomposition.csv. Industry/security contributions use the fixed complete [0,+1] all-security portfolio.

| event_id | date | tau | market_return | n | raw_quote_return | analytical_price_return | predicted_return | abnormal_return | portfolio |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| bbbee_draft_2026 | 2026-01-29 | 0 | 0.00144 | 160 | 0.00283 | 0.00283 | 0.00080 | 0.00203 | all |
| bbbee_draft_2026 | 2026-01-30 | 1 | -0.04154 | 160 | -0.01280 | -0.01280 | -0.02655 | 0.01375 | all |
