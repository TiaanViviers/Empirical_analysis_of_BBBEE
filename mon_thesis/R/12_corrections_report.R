write_corrections_report <- function(cfg) {
  root<-cfg$paths$outputs
  read_table<-function(name,directory='tables') {
    path<-file.path(root,directory,paste0(name,'.csv'))
    if(file.exists(path)) fread(path) else data.table()
  }
  headline<-read_table('headline_results_percent');inf<-read_table('event_study_inference')
  comparison<-read_table('headline_before_after');changes<-read_table('changed_market_models','diagnostics')
  actions<-read_table('corporate_action_application','diagnostics')
  daily<-read_table('primary_daily_decomposition');design<-read_table('placebo_design_summary','diagnostics')
  robust<-read_table('robustness_summary');placebos<-read_table('placebo_results')
  calibration_path<-file.path(root,'diagnostics/remediation/synchronous_calibration_summary.csv')
  calibration<-if(file.exists(calibration_path)) fread(calibration_path) else data.table()
  calibration_text<-'Calibration has not yet been executed for this handover; do not infer volatility robustness.'
  if(nrow(calibration)) {
    rate<-function(method_name,scenario_name) calibration[method==method_name & scenario==scenario_name,
      paste0(format(round(100*rejection_rate,2),nsmall=2),'%')][1]
    calibration_text<-paste0('Executed calibration: ',calibration$trials[1],' trials/scenario and ',calibration$securities[1],
      ' securities. Conditional-bootstrap rejection is ',rate('all','stable_gaussian'),' for the stable aggregate and ',
      rate('mining_minus_control','stable_gaussian'),' for the stable spread; under doubled event residual SD the rates are ',
      rate('all','event_all_residual_sd2'),' / ',rate('mining_minus_control','event_all_residual_sd2'),
      '. The KP-style aggregate rate is ',rate('kp_style_all','event_all_residual_sd2'),
      ' under proportional event scaling, ',rate('kp_style_all','centered_lognormal'),' under skewness and ',
      rate('kp_style_all','event_factor_sd2'),
      ' under factor-only event shocks. Its different estimand and these vulnerabilities prevent promotion to headline inference.')
  }
  test_path<-file.path(root,'diagnostics/test_run_metadata.json');test_current<-FALSE
  test_text<-'No matching post-run test stamp yet: run Rscript mon_thesis/tests/testthat.R.'
  if(file.exists(test_path)) {
    stamp<-jsonlite::read_json(test_path,simplifyVector=TRUE)
    hashes<-stamp$analysis_code_sha256
    code_current<-length(hashes)>0 && all(vapply(names(hashes),function(f)
      file.exists(f) && digest::digest(file=f,algo='sha256')==hashes[[f]],TRUE))
    test_current<-code_current && identical(stamp$inference_sha256,
      digest::digest(file=file.path(root,'tables/event_study_inference.csv'),algo='sha256'))
    if(test_current) test_text<-paste('Matched post-run tests:',stamp$cases,'cases;',stamp$passed,
      'passed expectations;',stamp$failed,'failed;',stamp$errors,'errors;',stamp$skipped,'skipped.')
  }
  complete<-nrow(headline)==5 && all(inf[headline_indices(inf,cfg),status]=='ok')
  status<-if(complete) 'All five events have supported revised baseline results.' else 'This is a selected-event/partial output set; run --all for the full handover.'
  summary<-if(nrow(comparison)) comparison[,.(event_id,estimate_before_pp=headline_estimate_pct_before,
    estimate_after_pp=headline_estimate_pct_after,change_pp=estimate_change_pp,
    raw_p_before=p_value_before,raw_p_after=p_value_after,holm_before=holm_primary_p_before,holm_after=holm_primary_p_after)] else data.table()
  m1<-if(nrow(changes)) changes[,.(event_id,instrument_id,alpha_before,alpha_after,beta_before,beta_after,sigma_before,sigma_after)] else data.table()
  revised<-headline[,.(event_id,n_mining,n_control,n_all,estimate_pct=headline_estimate_pct,
    ci_lower_pct,ci_upper_pct,p_value,holm_primary_p)]
  mask_path<-file.path(root,'diagnostics/remediation/extreme_mask_regression_comparison.csv')
  mask<-if(file.exists(mask_path)) fread(mask_path) else data.table()
  h2026<-headline[event_id=='bbbee_draft_2026']
  decomp<-daily[event_id=='bbbee_draft_2026' & portfolio=='all']
  groups<-read_table('primary_group_contributions')[event_id=='bbbee_draft_2026']
  if(nrow(groups)) groups[,`:=`(mean_car=100*mean_car,contribution_to_all_caar=100*contribution_to_all_caar)]
  sectors<-read_table('primary_industry_contributions')[event_id=='bbbee_draft_2026'][order(-contribution_to_all_caar)]
  if(nrow(sectors)) sectors<-sectors[seq_len(min(8,.N)),.(nature_of_business_raw,n,mean_car_pct=100*mean_car,
    contribution_pp=100*contribution_to_all_caar)]
  decomposition_text<-if(nrow(decomp)==2 && nrow(h2026)==1) paste0(
    'Day +1 contributes ',round(100*decomp[tau==1,abnormal_return]/sum(decomp$abnormal_return),1),
    '% of the 2026 CAAR. The sum of daily equal-security raw returns is ',
    round(100*sum(decomp$raw_quote_return),4),'%; positive abnormal performance is relative to the fitted benchmark, not a positive wealth change.') else ''
  meaningful<-if(nrow(robust)) robust[specification %in% c('reviewed_industry_proxy','partial_verified_issuer',
    'exclude_unresolved_action_securities','event_no_volume_screen','null_active_dates','event_sd_1p5','event_sd_2','donor_early','donor_late'),
    .(event_id,specification,n,estimate,se,p_value,status)] else data.table()
  lines<-c('# Methodological corrections and statistical remediation','',
    'Prepared for independent re-review. The immutable source package and event register are unchanged. The pre-remediation code, tables, diagnostics, figures and local derived data are archived in outputs/baselines/pre_remediation_2026-11-24/.','',
    '## Overall status','',status,
    'Deterministic defects M2/S1/N1 are corrected. M1 is corrected for the verified Reinet conversion but remains partial for distributions, rights and provider conventions. Timing, news, exposure and selection audits are implemented; causal identification and complete historical mappings remain unresolved. Conditional bootstrap inference is retained; no volatility-robust guarantee is claimed.','',
    '## Primary choices and updated results','',
    'Preferred return: security-unit-consistent price return. Verified unit conversions are applied from research/corporate_actions_v1.csv; raw closes and raw returns are retained. Cash distributions are not selectively added to an otherwise price-only series. This is not total shareholder return.',
    'Primary inference retains the original absolute-tail bootstrap p-value. The reported symmetric interval now inverts that same finite-draw p<0.05 rule. The five-session synchronous bootstrap includes OLS fitting error and the actual fit/event gap. Full baseline inference uses 4,999 draws; see each inference row for actual replication counts.',
    'The five registered [0,+1] hypotheses are fixed in config/headline_hypotheses.csv, independently of selected events. Intervals are pointwise; Holm conclusions address the five-test family.',
    '',md_table(revised,5),'',
    'Mining estimates are percentage-point mining-minus-control differences; other rows are aggregate CAAR in percent. Security counts are not verified issuer counts.',
    '', '## Before and after','',md_table(summary,6),'',
    'Before intervals used equal-tailed basic quantiles while p-values used absolute tails. After intervals use absolute-tail inversion. Thus interval changes are not all consequences of the Reinet correction. Isolated convention and donor-mask comparisons are recorded separately under diagnostics/remediation/.',
    '', '## M1 — Return measurement','',
    'The original RNI 29 November 2017 ratio was +886.1667%. The official FTSE/JSE notice confirms ten depositary receipts became one ordinary share. Only that date is adjusted: gross raw return divided by 10 gives −1.3833%. No source price changes and no guessed corporate-action factors are used.',
    'The ledger records version, effective date, type, factor/cash amount, units, evidence, verification status, application status and unresolved cases. corporate_action_application.csv is the executed audit. Reinet corrections propagate through model fitting, residual donors, AR/CAR/CAAR and inference.',
    'MTNZF R20 capital distribution and Aveng rights ex-date are verified actions, but a provider-consistent return adjustment is unresolved. They remain explicit price-series limitations with a targeted security-exclusion sensitivity. Lonmin’s influential jump has no verified factor and is retained. The documented Steinhoff news collapse is not automatically corrected away.',
    '',md_table(m1,7),'',
    'JSE distinguishes J203 All Share from J203T Total Return, supporting price-index-compatible intent. The exact IRESS exported variant and equity distribution conventions still require provider verification; benchmark_convention_audit.csv states this limitation.',
    '', '## M2 — Complete extreme-deletion mask','',
    'Fit/event usability and donor validity are now separate fields. Full extreme deletion sets both false; the bootstrap constructs its complete-date donor matrix only from eligible donor residuals. Baseline volume policy remains separate. New regression tests prove a flagged observation cannot re-enter the null.',
    'The reviewer’s numerical mask diagnostic is reproduced on preserved ORIGINAL prices, isolating the defect from conversion changes. New production sensitivities additionally use the revised analytical returns, so their values need not match those old-price diagnostics.',
    '',md_table(mask,7),'',
    '## M3/M4 — Information timing and economic interpretation','',
    'Official publication dates remain the baseline. A sourced chronology distinguishes the 2018 Cabinet reference, public 21 September stimulus/approval statement, 26 September advisory and 27 September gazetting. Earlier windows are exploratory information-event comparisons, never selected by significance.',
    'timing_comparisons.csv provides re-estimated comparisons; fixed_sample_2018_timing.csv freezes baseline coefficients and common constituents to isolate timing. The negative gazette window is not a stable negative reaction to the entire 2018 information sequence.',
    'The 2017 two sessions are 15 and 19 June. News records identify 2023 diplomatic overlap, 2025 tariff-related outlook information with intraday caveats, and 2026 domestic/global monetary and market developments. Date overlap is not proof of a causal price effect.',
    decomposition_text,'',md_table(decomp,6),'',
    'primary_security_contributions.csv and primary_industry_contributions.csv show concentration on fixed complete samples. No additional external return dataset was imported. The market-adjusted alternative uses existing J203 data; it imposes different normal-return restrictions and does not isolate policy news.',
    'The 2026 group and largest industry contributions below are in percent/percentage points; they show heterogeneous relative performance, not measured legal policy exposure. Banks and REITs are important contributors, while the source-classified mining group has a negative average CAR.',
    '',md_table(groups,5),'',md_table(sectors,5),'',
    '', '## M5 — Uncertainty and alternative inference','',
    'Conditional synchronous inference remains primary. Added scenarios vary block length, early/late donor periods, all-active donor dates and EVENT-INNOVATION SD multipliers 1.5/2; the multiplier does not scale OLS estimation error. These are scenarios, not estimated event-volatility adjustments.',
    'A restricted BMP/KP-style standardized-CAR diagnostic is supplied for aggregate portfolios only. It concerns mean standardized CAR, not the signed mining/control contrast or raw equal-security CAAR. It assumes temporally independent innovations and representative cross-sectional correlation. It is not silently substituted as primary, and its unadjusted exploratory p-values do not create headline discoveries.',
    'Synchronous multi-security calibration uses common and mining-sector shocks, different firm fit masks, heavy tails, serial dependence, and both proportional event-volatility and factor-only correlation changes. All simulations have zero true mean effect. Rejection and coverage Monte Carlo intervals are reported; these do not estimate real-data false-positive rates.',
    calibration_text,
    '',md_table(calibration,5),'',
    '## S1/S2/S3/S4/N1 — Additional corrections','',
    'S1: asymmetric/tied-distribution tests verify agreement of primary p-values and confidence intervals. Legacy basic intervals and equal-tail probabilities remain auxiliary columns for comparison, not alternative primary evidence.',
    'S2: a versioned event-dated security/issuer/exposure ledger records verified and unresolved evidence. Baseline source-industry groups and equal-security weights remain explicit. The reviewed industry alternative moves verified KIO mining operations into mining and excludes manufacturing Hulamin from the direct-mining proxy; neither establishes uniform legal treatment. Partial issuer weighting combines only verified Fortress A/B classes. Unknown historic identifiers are not assigned using current names.',
    'S3: pseudo-event fitting windows now exclude their own real policy event. Fixed candidate horizons and spacing can produce fewer than ten dates for 2017; shortfalls are reported, not filled with contaminated windows. Frozen classifications and other news remain limitations. The unavailable 29 December 2023 EE-final placebo remains N=0/NA because J203 is missing on 2 January 2024.',
    '',md_table(design),'',
    'S4: separate event-only and donor-only volume sensitivities isolate observability choices from fit-period liquidity. Existing minimum-observation and unchanged-price screens remain configurable. The target is eligible observable/liquid JSE securities, not a survivorship-free universe of South African firms.',
    'N1: an explicit five-row hypothesis registry determines headline membership and Holm family size. Custom event lists and single-event runs cannot reduce the family; tests cover narrow configurations.',
    '', '## Selected sensitivities','',md_table(meaningful,6),'',
    'All rows in this section are exploratory. Their individual p-values do not correct for searching across specifications. Larger or smaller p-values were not a criterion for selecting the correction method.',
    'The 2026 positive point estimate persists across many same-date screens, but its raw p is sensitive to donor selection and volatility assumptions: inspect the all-active donor and event-SD scenarios rather than treating baseline significance as universal. No scenario is selected to obtain or remove significance.',
    '', '## Validation and reproduction','',test_text,
    'The pre-correction all-event run and 331-expectation tests reproduced before analytical edits. All nine original CSV tables were byte-identical; the archive includes code/config/source fingerprints and reproduction logs.',
    'Current independent NumPy OLS/return/CAR checks, component regressions, p/interval checks, CLI selection checks and source/archival preservation evidence are under outputs/diagnostics/remediation/. Run-specific code/config/ledger hashes are in diagnostics/run_metadata.json. Tests carry an inference-table and code fingerprint to prevent stale pass claims.',
    '', 'From the repository root:', '', '```sh',
    'Rscript mon_thesis/run_analysis.R --all',
    'Rscript mon_thesis/tests/testthat.R',
    'Rscript mon_thesis/review/remediation/validate_components.R',
    'iress-export/.venv/bin/python mon_thesis/review/remediation/verify_corrected.py',
    'Rscript mon_thesis/review/remediation/calibrate_inference.R',
    'Rscript mon_thesis/review/remediation/finalize_handover.R', '```','',
    'Single-event interface remains Rscript mon_thesis/run_analysis.R --event mining_charter_2017. It overwrites latest-run aggregates; use an isolated copy for comparisons. See review/remediation/README.md for portable Python selection and archive restoration.',
    '', '## Remaining limitations and next review priorities','',
    '1. Highest priority: provider-adjustment conventions, complete capital/rights/distribution histories and economically consistent equity/benchmark returns. Only the sourced security-unit correction is approved here.',
    '2. First disclosures and concurrent news, especially 2018 approval/stimulus versus gazetting and the 2026 stress-day contribution. Two daily observations do not isolate a causal policy effect or identify event volatility.',
    '3. Historical security/issuer identities, legal/geographic exposure and selection into observable/liquid event samples. Dated workforce/compliance/financial controls remain absent.',
    '4. Independent assessment of the conditional residual process, block choice, standardized diagnostic assumptions, finite-draw inversion and simulation design. A passing implementation does not settle these research assumptions.',
    '', '## Research readiness','',
    'Suitable for independent methodological re-review and preliminary supervisor discussion, accompanied by the explicit partial/unresolved items. Not thesis-final causal or efficiency-cost evidence. Failure to reject is not proof of no economic effect. No full reader-facing R Markdown report was written in this pass.',
    '', 'Research choices, alternatives and required supervisor decisions are recorded in docs/research_decisions.md. No remote push, licensed-data distribution or supervisor contact was performed.')
  write_md(lines,file.path(root,'reports/methodological_corrections_report.md'))
  write_md(c('# Execution report — methodological correction pass','',status,'',
    'This report supersedes the pre-remediation execution report. The original report and results are retained in outputs/baselines/pre_remediation_2026-11-24/.',
    'Read methodological_corrections_report.md for issue-by-issue changes, before/after results, calibration, unresolved limitations and reproduction commands. The historical independent_methodology_review.md remains the review of the earlier implementation.',
    '',md_table(revised,5),'',test_text,'',
    paste('Baseline inference rows:',nrow(inf),'; unavailable:',sum(inf$status!='ok')),
    paste('Sensitivity rows:',nrow(robust),'; placebo attempts:',nrow(placebos),'; valid:',if(nrow(placebos))sum(placebos$status=='ok') else 0),
    'Source package fingerprints must agree before/after every run. Readiness: independent re-review and preliminary discussion; not thesis-final or causal efficiency evidence.'),
    file.path(root,'reports/execution_report.md'))
  invisible(list(tests_current=test_current,complete=complete))
}
