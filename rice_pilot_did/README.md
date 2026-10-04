# Rice crop insurance pilot (2009) and paddy-rice planted area

Exploratory difference-in-differences on municipal paddy-rice planted area, 2000–2011.
These are feasibility estimates for the thesis, not final causal results.

- **Pilot group:** the 17 usable municipalities where rice insurance was first offered in 2009.
- **Comparison group:** 42 municipalities that were not on the 2011 list of 30 and first became eligible in 2012, screened to the pilots' range of pre-period area.
- **Excluded:** the ten municipalities that entered in 2011 are dropped from both groups.

## Main result

| | Value |
|---|---:|
| Coefficient on log area | 0.0306 |
| Municipality-clustered SE | 0.0208 |
| p-value, t(58) | 0.147 |
| Relative change | +3.1% (95% CI −1.1% to +7.5%) |

The pre-period scale gap (Figure 5) and the pre-trends (Figure 2) mean this should not be read as a causal effect yet. See `docs/README_results.md` (Korean) for the full discussion.

## Folder structure

```
rice_pilot_did/
├── R/
│   ├── 00_setup_theme.R     shared ggplot theme, colours, export helper
│   └── 01_make_figures.R    builds all six figures
├── figures/                 PNG (300 dpi) and PDF for each figure
├── data/
│   ├── results/             estimates, event study, leave-one-out, descriptives, summary.json
│   └── panel/               analysis panels and parsed KOSIS source rows
├── python/analyze.py        estimation code that produced data/results
└── docs/                    protocol.md (rules written before estimation), README_results.md
```

## Figures

| File | Content |
|---|---|
| `fig_rice_01_indexed_trajectories` | Geometric-mean area index by group, 2008 = 100 |
| `fig_rice_02_event_study` | Pilot × year coefficients relative to 2008, pointwise 95% CIs |
| `fig_rice_03_specification_estimates` | Main estimate and all pre-specified sensitivity models |
| `fig_rice_04_leave_one_out` | Main model dropping one pilot municipality at a time |
| `fig_rice_05_pre_period_scale` | Mean 2000–2008 area per municipality, by group |
| `fig_rice_06_mean_area_by_period` | Mean planted area before and after 2009, by group |

The style follows `insurance_graph` in the repository root: `theme_bw(base_size = 14)`, grey40 border, grey90/grey95 grid, `#66C2A5` as the main colour and comma-formatted axes. Following the Stata figures, the source note sits at the bottom left, the legend sits in one row at the top, and bars carry value labels. Figures carry no in-plot title, so numbered captions can be added in the thesis.

## Reproduce

Requirements: R ≥ 4.2 and ggplot2 ≥ 3.4 (scripts use `linewidth`).

```bash
cd rice_pilot_did
Rscript R/01_make_figures.R
```

Run R in a UTF-8 locale; RStudio and R ≥ 4.2 on Windows do this by default. The pilot municipality ids contain Korean names, which the scripts translate to English for the figures.

To re-estimate from the KOSIS file (DT_1ET0033), run `python python/analyze.py --source <path to xls>` with numpy, scipy, pandas and matplotlib installed. The source file itself is not included. Its SHA-256 hash is recorded in `data/results/summary.json`.
