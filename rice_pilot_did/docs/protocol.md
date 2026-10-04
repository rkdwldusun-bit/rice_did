# Rice availability analysis: exploratory protocol, 2026-10-04

Written after inspecting coverage and administrative discontinuities, before estimating effects in this analysis. This is not prospective preregistration: earlier national-crop results were known. No specification will be chosen by significance.

- Outcome: log municipal paddy-rice planted area (ha), KOSIS DT_1ET0033 uploaded XLS. Equal municipality weights; no imputation of absent or zero values.
- Target: 2009 insurance availability cohort versus municipalities absent from the verified 2011 list, hence first nationally eligible in 2012. Exclude the entire 2011 cohort from this comparison. Actual uptake and payments are unobserved.
- Main window: 2000-2011; post=2009-2011. No untreated comparison claimed after 2012.
- Municipalities only, within the eight ordinary mainland provinces. Exclude national/provincial totals, metropolitan aggregates and Jeju. Require positive observations throughout each analysis window.
- Main boundary exclusions: Nonsan/Gyeryong, Goesan/Jeungpyeong and Changwon/Masan/Jinhae because the supplied series changes geographic coverage in the window. No arbitrary zero-filling or treated/untreated mergers. Cheongwon and Cheongju stay separate.
- Main controls: additionally restrict control pre-2009 mean area to the min-max interval of the usable early-treated municipalities. This is a scale screen, not proof of common support or balance. All treated units retained.
- Main model: municipality and year fixed effects; equal weights; municipality-clustered CR1 standard errors, t(G-1) reference. Report province-clustered sensitivity (8 clusters; approximate and fragile).
- Precommitted sensitivities: all eligible controls without scale screen; province-by-year fixed effects; same screened sample 2006-2011; fresh 2006-2011 sample allowing Nonsan, Gyeryong, Goesan and Jeungpyeong, still excluding the Changwon merger.
- Event study: each treated-by-year coefficient relative to 2008; pointwise 95% intervals; joint pre-2008 Wald F test. A nonsignificant pretest does not validate parallel trends.
- Preperiod differential linear trend and 2006 placebo on 2000-2008. Leave out each treated municipality once; do not select exclusions from their effect on results.
- 2009 decision timing is uncertain; also report 2010-2011 excluding 2009. Public 2011 release explicitly permits enrollment after planting; therefore availability-year acreage responses need care.
- Descriptive approximate MDE: (t_0.975,G-1 + z_0.80)*estimated SE, not prospective power or evidence for a null effect.
- All results are exploratory feasibility estimates. Weather, announcement dates, administrative definitions and source anomalies require further checks before causal claims.
