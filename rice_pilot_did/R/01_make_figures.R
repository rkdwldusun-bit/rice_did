###############################################################
# 01_make_figures.R
# Rice crop insurance pilot (2009) vs. 2012 municipalities
# Exploratory DiD on log paddy-rice planted area, 2000-2011
#
# Inputs : data/results/*.csv, data/results/summary.json,
#          data/panel/analysis_panel_main.csv
#          (all produced by python/analyze.py)
# Outputs: figures/fig_rice_0X_*.png and .pdf
#
# Run from the rice_pilot_did/ folder:
#   Rscript R/01_make_figures.R
###############################################################

source(file.path("R", "00_setup_theme.R"), encoding = "UTF-8")

# ---- Small reader for numeric values in summary.json ---------
# (avoids an extra jsonlite dependency)
summary_txt <- paste(readLines(file.path(dir_results, "summary.json"),
                               encoding = "UTF-8"), collapse = "")
json_num <- function(key) {
  m <- regmatches(summary_txt,
                  regexpr(paste0('"', key, '"\\s*:\\s*-?[0-9.eE+-]+'), summary_txt))
  as.numeric(sub('.*:\\s*', "", m))
}
pre_F  <- json_num("pretrend_joint_F")
pre_p  <- json_num("pretrend_joint_p")
wild_p <- json_num("province_wild_p")


###############################################################
# Figure 1. Indexed trajectories (2008 = 100)
###############################################################

traj <- read_utf8(file.path(dir_results, "indexed_trajectories.csv"))
# columns: year, "0" = 2012 municipalities, "1" = 2009 pilot
traj_long <- rbind(
  data.frame(year = traj$year, index = traj[["1"]], group = "2009 pilot municipalities"),
  data.frame(year = traj$year, index = traj[["0"]], group = "2012 municipalities")
)
traj_long$group <- factor(traj_long$group, levels = names(group_colours))

# value labels only at the start, reference and end years
traj_lab <- subset(traj_long, year %in% c(2000, 2011))
traj_lab$label <- formatC(traj_lab$index, format = "f", digits = 1)
is_pilot <- traj_lab$group == "2009 pilot municipalities"
# 2000: labels above/below the points; 2011: labels to the right
traj_lab$x     <- ifelse(traj_lab$year == 2011, 2011.2, 2000)
traj_lab$hjust <- ifelse(traj_lab$year == 2011, 0, 0.5)
traj_lab$vjust <- ifelse(traj_lab$year == 2000, ifelse(is_pilot, 1.9, -1.0),
                         ifelse(is_pilot, 0.1, 0.9))

fig1 <- ggplot(traj_long, aes(x = year, y = index, color = group)) +
  geom_vline(xintercept = 2008.5, linetype = "dashed", color = col_reference, linewidth = 0.6) +
  annotate("text", x = 2008.6, y = 113.5, label = "Pilot insurance\navailable (2009)",
           hjust = 0, vjust = 1, size = 3.4, color = "grey30") +
  geom_line(linewidth = 0.9) +
  geom_point(size = 2.5) +
  geom_text(data = traj_lab, aes(x = x, label = label, hjust = hjust, vjust = vjust),
            size = 3.4, show.legend = FALSE) +
  scale_color_manual(values = group_colours) +
  scale_x_continuous(breaks = 2000:2011, limits = c(1999.6, 2011.8)) +
  scale_y_continuous(breaks = seq(90, 115, by = 5), limits = c(88, 115),
                     expand = expansion(mult = c(0, 0.02))) +
  labs(x = "Year",
       y = "Area index (2008 = 100)",
       caption = paste0("Note: Geometric mean of paddy-rice planted area by group; ",
                        "17 pilot and 42 comparison municipalities.\n", note_kosis)) +
  theme_thesis(legend = "top")

save_figure(fig1, "fig_rice_01_indexed_trajectories", width = 8.5, height = 5.2)


###############################################################
# Figure 2. Event study (2008 reference year)
###############################################################

ev <- read_utf8(file.path(dir_results, "event_study.csv"))
ev$period <- ifelse(ev$year < 2009, "Pre-pilot", "Post-pilot")
ev_ref <- data.frame(year = 2008, beta = 0)

fig2 <- ggplot(ev, aes(x = year, y = beta)) +
  geom_hline(yintercept = 0, color = "grey40", linewidth = 0.5) +
  geom_vline(xintercept = 2008.5, linetype = "dashed", color = col_reference, linewidth = 0.6) +
  geom_errorbar(aes(ymin = ci_low, ymax = ci_high), width = 0.25,
                color = col_treated, linewidth = 0.8) +
  geom_point(size = 2.8, color = col_treated) +
  geom_point(data = ev_ref, size = 2.8, shape = 21, fill = "white", color = "grey40") +
  scale_x_continuous(breaks = 2000:2011) +
  scale_y_continuous(breaks = seq(-0.10, 0.06, by = 0.02),
                     labels = function(x) formatC(x, format = "f", digits = 2)) +
  labs(x = "Year",
       y = "Difference in log area (2008 = 0)",
       caption = paste0(
         "Note: Coefficients on pilot x year with municipality and year fixed effects; ",
         "pointwise 95% CIs, municipality-clustered SE, t(58).\n",
         "Joint test of 2000-2007 coefficients: F(8, 58) = ",
         formatC(pre_F, format = "f", digits = 2), ", p = ",
         formatC(pre_p, format = "f", digits = 3),
         ". A non-rejection does not establish parallel trends.\n", note_kosis)) +
  theme_thesis()

save_figure(fig2, "fig_rice_02_event_study", width = 8.5, height = 5.4)


###############################################################
# Figure 3. Estimates across specifications (% change, 95% CI)
###############################################################

est <- read_utf8(file.path(dir_results, "estimates.csv"))
spec_labels <- c(
  "Main: pre-area screen, 2000-2011"        = "Main: scale-screened controls, 2000-2011",
  "Main, province clusters"                 = "Main, province-clustered SE (8 clusters)",
  "All stable eligible controls"            = "All eligible controls (no scale screen)",
  "Province-by-year FE"                     = "Province-by-year fixed effects",
  "Same sample, 2006-2011"                  = "Same municipalities, 2006-2011",
  "2006-2011, include split municipalities" = "2006-2011, incl. split municipalities",
  "Exclude 2009 transition year"            = "Excluding 2009 transition year"
)
est$label <- factor(spec_labels[est$model], levels = rev(spec_labels))
est$type  <- ifelse(est$model == "Main: pre-area screen, 2000-2011", "Main",
             ifelse(est$model == "All stable eligible controls",
                    "Different comparison group", "Sensitivity"))
est$text  <- paste0(formatC(est$percent, format = "f", digits = 1), "%  (p ",
                    ifelse(est$p < 0.001, "< 0.001", paste("=", formatC(est$p, format = "f", digits = 3))), ")")
type_colours <- c("Main" = col_treated, "Sensitivity" = "grey40",
                  "Different comparison group" = col_control)

fig3 <- ggplot(est, aes(x = percent, y = label, color = type)) +
  geom_vline(xintercept = 0, color = "grey40", linewidth = 0.5) +
  geom_errorbarh(aes(xmin = percent_low, xmax = percent_high), height = 0.25, linewidth = 0.8) +
  geom_point(size = 2.8) +
  geom_text(aes(x = percent_high, label = text), hjust = -0.1, size = 3.4,
            color = "grey20", show.legend = FALSE) +
  scale_color_manual(values = type_colours, breaks = names(type_colours)) +
  scale_x_continuous(breaks = seq(-5, 30, by = 5), limits = c(-5, 32),
                     labels = function(x) paste0(x, "%")) +
  labs(x = "Relative change in planted area (%), 95% CI",
       y = NULL,
       caption = paste0(
         "Note: Percent = 100 x [exp(beta) - 1]. Province wild cluster bootstrap ",
         "(256 Rademacher draws) for the main model: p = ",
         formatC(wild_p, format = "f", digits = 3), ".\n",
         "The no-screen estimate compares pilots with a different, less comparable control group; ",
         "its significance is not a reason to prefer it.\n", note_kosis)) +
  theme_thesis(legend = "top") +
  theme(axis.text.y = element_text(size = 11, color = "grey20"),
        panel.grid.major.y = element_blank())

save_figure(fig3, "fig_rice_03_specification_estimates", width = 9.5, height = 5.4)


###############################################################
# Figure 4. Leave-one-treated-municipality-out
###############################################################

loo <- read_utf8(file.path(dir_results, "leave_one_treated_out.csv"))
main_pct <- est$percent[est$model == "Main: pre-area screen, 2000-2011"]
loo$name  <- unname(treated_names[loo$model])
if (anyNA(loo$name)) stop("Korean municipality ids did not match. Run R in a UTF-8 locale ",
                          "(RStudio default; R >= 4.2 on Windows) and save scripts as UTF-8.")
loo$name  <- factor(loo$name, levels = loo$name[order(loo$percent)])

fig4 <- ggplot(loo, aes(x = percent, y = name)) +
  geom_vline(xintercept = 0, color = "grey40", linewidth = 0.5) +
  geom_vline(xintercept = main_pct, linetype = "dashed", color = col_treated, linewidth = 0.7) +
  geom_errorbarh(aes(xmin = percent_low, xmax = percent_high), height = 0.3,
                 color = "grey55", linewidth = 0.7) +
  geom_point(size = 2.6, color = col_treated) +
  geom_text(data = data.frame(percent = main_pct, name = levels(loo$name)[nlevels(loo$name)]),
            label = paste0("Main estimate: ", formatC(main_pct, format = "f", digits = 1), "%"),
            hjust = -0.05, vjust = -1.4, size = 3.4, color = "grey20") +
  scale_x_continuous(breaks = seq(-4, 12, by = 2), labels = function(x) paste0(x, "%")) +
  scale_y_discrete(expand = expansion(add = c(0.6, 1.4))) +
  labs(x = "Relative change in planted area (%), 95% CI",
       y = "Pilot municipality omitted",
       caption = paste0("Note: Main model re-estimated 17 times, each time dropping one ",
                        "pilot municipality; exclusions were not selected by their effect.\n",
                        note_kosis)) +
  theme_thesis() +
  theme(axis.text.y = element_text(size = 11, color = "grey20"),
        panel.grid.major.y = element_blank())

save_figure(fig4, "fig_rice_04_leave_one_out", width = 8, height = 6)


###############################################################
# Figure 5. Pre-period scale: mean area 2000-2008 by municipality
###############################################################

panel <- read_utf8(file.path(dir_panel, "analysis_panel_main.csv"))
pre   <- aggregate(area ~ id + treated, data = subset(panel, year < 2009), FUN = mean)
pre$group <- factor(ifelse(pre$treated == 1, "2009 pilot municipalities", "2012 municipalities"),
                    levels = rev(names(group_colours)))
control_max <- max(pre$area[pre$treated == 0])
n_above     <- sum(pre$area[pre$treated == 1] > control_max)
n_treated   <- sum(pre$treated == 1)

above <- subset(pre, treated == 1 & area > control_max)
set.seed(2009)
fig5 <- ggplot(pre, aes(x = area, y = group, color = group)) +
  geom_vline(xintercept = control_max, linetype = "dashed", color = "grey40", linewidth = 0.6) +
  geom_text(data = data.frame(area = control_max,
                              group = factor("2009 pilot municipalities", levels = levels(pre$group))),
            label = paste0("Largest comparison municipality (",
                           fmt_comma(round(control_max)), " ha):\n", n_above, " of ",
                           n_treated, " pilot municipalities are larger"),
            hjust = -0.04, vjust = -0.9, size = 3.4, color = "grey20") +
  geom_point(position = position_jitter(height = 0.12, width = 0), size = 2.6, alpha = 0.85) +
  scale_color_manual(values = group_colours) +
  scale_x_continuous(labels = fmt_comma, breaks = seq(0, 25000, by = 5000),
                     limits = c(4000, 25000)) +
  labs(x = "Mean paddy-rice planted area, 2000-2008 (ha)",
       y = NULL,
       caption = paste0("Note: Comparison municipalities were screened to the pilot range ",
                        "of pre-period mean area; this is a scale screen, not matching.\n",
                        note_kosis)) +
  theme_thesis() +
  scale_y_discrete(expand = expansion(add = c(0.5, 0.9))) +
  theme(axis.text.y = element_text(size = 12, color = "grey20"),
        panel.grid.major.y = element_blank())

save_figure(fig5, "fig_rice_05_pre_period_scale", width = 8.5, height = 4.6)


###############################################################
# Figure 6. Mean planted area before and after the pilot
#           (bar + value-label layout from the Stata reference)
###############################################################

desc <- read_utf8(file.path(dir_results, "descriptives.csv"))
desc$group  <- factor(ifelse(desc$group == "2009 cohort", "2009 pilot municipalities",
                             "2012 municipalities"), levels = names(group_colours))
desc$period <- factor(ifelse(grepl("^pre", desc$period), "2000-2008", "2009-2011"),
                      levels = c("2000-2008", "2009-2011"))
desc$label  <- fmt_comma(round(desc$mean_ha))

fig6 <- ggplot(desc, aes(x = period, y = mean_ha, fill = group)) +
  geom_col(position = position_dodge(width = 0.7), width = 0.6, color = NA) +
  geom_text(aes(label = label), position = position_dodge(width = 0.7),
            vjust = -0.5, size = 3.6, color = "black") +
  scale_fill_manual(values = group_colours) +
  scale_y_continuous(labels = fmt_comma, breaks = seq(0, 16000, by = 4000),
                     limits = c(0, 16500), expand = expansion(mult = c(0, 0.03))) +
  labs(x = "Period",
       y = "Mean planted area (ha)",
       caption = paste0("Note: Unweighted municipality-year means; ",
                        "17 pilot and 42 comparison municipalities.\n", note_kosis)) +
  theme_thesis(legend = "top") +
  theme(panel.grid.major.x = element_blank())

save_figure(fig6, "fig_rice_06_mean_area_by_period", width = 7.5, height = 5)

message("All figures written to ", normalizePath(dir_figures))
