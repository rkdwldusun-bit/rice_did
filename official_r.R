# NOT EXECUTED here: R/Rscript is absent in the analysis runtime.
# Requires installed did and HonestDiD packages. This script does not install them.
# Run from this folder: Rscript official_r.R
stopifnot(requireNamespace('did',quietly=TRUE),requireNamespace('HonestDiD',quietly=TRUE))
set.seed(20261004)
dir.create('official_R_outputs',showWarnings=FALSE)
d <- read.csv('cs_input.csv',check.names=FALSE)
# Preserve actual availability year in cohort; encode untreated-through-2011 as 0
# only for software. These units are not permanently untreated.
d$g_software <- ifelse(d$cohort==2012,0,d$cohort)
cs <- did::att_gt(yname='log_area',tname='year',idname='uid',gname='g_software',
                 data=d,xformla=~1,control_group='notyettreated',
                 base_period='universal',anticipation=0,est_method='reg',
                 panel=TRUE,allow_unbalanced_panel=FALSE,
                 clustervars='uid',bstrap=TRUE,biters=9999,cband=TRUE)
saveRDS(cs,'official_R_outputs/cs_result.rds')
tab <- data.frame(g=cs$group,t=cs$t,beta=cs$att,se=cs$se)
write.csv(tab,'official_R_outputs/cs_cells.csv',row.names=FALSE)
ref <- read.csv('group_time_att.csv')
cmp <- merge(ref[,c('g','t','beta')],tab,by=c('g','t'),suffixes=c('_python','_R'))
stopifnot(nrow(cmp)==4,max(abs(cmp$beta_python-cmp$beta_R))<1e-8)
# SEs need not be identical: package multiplier scaling and finite-sample
# conventions differ from the explicitly documented custom IF calculation.
capture.output(summary(cs),file='official_R_outputs/cs_summary.txt')

beta <- read.csv('honest_beta.csv')
sigma <- as.matrix(read.csv('honest_covariance.csv',row.names=1,check.names=FALSE))
stopifnot(identical(as.character(beta$year),rownames(sigma)),
          identical(as.character(beta$year),colnames(sigma)),
          nrow(sigma)==11,nrow(beta)==11,all(is.finite(sigma)))
original <- HonestDiD::constructOriginalCS(betahat=beta$beta,sigma=sigma,
                  numPrePeriods=8,numPostPeriods=3,l_vec=rep(1/3,3),alpha=.05)
robust <- HonestDiD::createSensitivityResults_relativeMagnitudes(
                  betahat=beta$beta,sigma=sigma,numPrePeriods=8,numPostPeriods=3,
                  l_vec=rep(1/3,3),Mbarvec=c(0,.5,1,1.5,2),alpha=.05)
write.csv(original,'official_R_outputs/HonestDiD_original.csv',row.names=FALSE)
write.csv(robust,'official_R_outputs/HonestDiD_relative_magnitudes.csv',row.names=FALSE)
saveRDS(list(original=original,robust=robust),'official_R_outputs/HonestDiD_results.rds')
capture.output(sessionInfo(),file='official_R_outputs/sessionInfo.txt')
