###############################################################
# 00_setup_theme.R
# Shared settings for all rice pilot DiD figures
#
# Style follows MY_R_STYLE_REFERENCE (insurance_graph):
#   theme_bw(base_size = 14), grey40 panel border, grey90/grey95
#   grid, black axis titles, grey30 axis text, white background,
#   comma-formatted numbers, no in-plot title.
# From the Stata reference: source note at bottom-left,
#   one-row legend at the top, value labels where useful.
#
# Requires: ggplot2 (>= 3.4, uses `linewidth`)
###############################################################

library(ggplot2)

# ---- Paths ---------------------------------------------------
# Run all scripts from the rice_pilot_did/ folder
# (or set the working directory there in RStudio).
dir_results <- file.path("data", "results")
dir_panel   <- file.path("data", "panel")
dir_figures <- "figures"
dir.create(dir_figures, showWarnings = FALSE)

# ---- Colours -------------------------------------------------
# #66C2A5 is the colour used in the reference ggplot figure
# (first colour of ColorBrewer Set2); #FC8D62 is its partner.
col_treated   <- "#66C2A5"   # 2009 pilot municipalities
col_control   <- "#FC8D62"   # 2012 municipalities
col_reference <- "grey55"    # reference year / reference lines

group_colours <- c(
  "2009 pilot municipalities" = col_treated,
  "2012 municipalities"       = col_control
)

# ---- Number formats ------------------------------------------
fmt_comma <- function(x) format(x, big.mark = ",", scientific = FALSE, trim = TRUE)
fmt_pct   <- function(x) paste0(formatC(x, format = "f", digits = 1), "%")

# ---- Source notes --------------------------------------------
note_kosis <- "Source: KOSIS DT_1ET0033 (paddy rice planted area by municipality); author's estimation."

# ---- Theme ---------------------------------------------------
theme_thesis <- function(base_size = 14, legend = "none") {
  theme_bw(base_family = "sans", base_size = base_size) +
    theme(
      plot.title         = element_blank(),
      panel.border       = element_rect(color = "grey40", fill = NA, linewidth = 0.8),
      panel.grid.major   = element_line(color = "grey90", linewidth = 0.6),
      panel.grid.minor   = element_line(color = "grey95", linewidth = 0.4),
      axis.title         = element_text(size = 15, color = "black"),
      axis.text          = element_text(size = 11, color = "grey30"),
      axis.text.x        = element_text(angle = 0, hjust = 0.5, vjust = 0.5),
      legend.position    = legend,
      legend.direction   = "horizontal",
      legend.title       = element_blank(),
      legend.text        = element_text(size = 11),
      legend.background  = element_rect(fill = "white", color = NA),
      legend.key         = element_rect(fill = "white", color = NA),
      plot.caption       = element_text(size = 9, color = "grey30", hjust = 0),
      plot.caption.position = "plot",
      plot.background    = element_rect(fill = "white", color = NA),
      panel.background   = element_rect(fill = "white", color = NA)
    )
}

# ---- Export helper -------------------------------------------
# PNG (2400 px wide, as in the Stata exports) + vector PDF.
save_figure <- function(plot, name, width = 8, height = 5) {
  ggsave(file.path(dir_figures, paste0(name, ".png")), plot,
         width = width, height = height, dpi = 300, bg = "white")
  ggsave(file.path(dir_figures, paste0(name, ".pdf")), plot,
         width = width, height = height, bg = "white")
  message("Saved: ", name)
}

# ---- English names for the treated municipalities ------------
# (ids in the data are province code + Korean name)
treated_names <- c(
  "GG_평택시" = "Pyeongtaek", "GG_이천시" = "Icheon",
  "GW_철원군" = "Cheorwon",
  "CB_청원군" = "Cheongwon",  "CB_진천군" = "Jincheon",
  "CN_당진군" = "Dangjin",    "CN_서산시" = "Seosan",
  "JB_김제시" = "Gimje",      "JB_부안군" = "Buan",      "JB_익산시" = "Iksan",
  "JN_나주시" = "Naju",       "JN_영암군" = "Yeongam",   "JN_해남군" = "Haenam",
  "GB_구미시" = "Gumi",       "GB_상주시" = "Sangju",
  "GN_김해시" = "Gimhae",     "GN_밀양시" = "Miryang"
)

read_utf8 <- function(path) read.csv(path, encoding = "UTF-8", check.names = FALSE)
