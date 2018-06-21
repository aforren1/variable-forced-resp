library(ggplot2)
library(ggridges)
source('preprocess.r')
source('misc.r')

all_data <- preprocess()

practice_data <- all_data[['practice_data']]
practice_data <- practice_data[stim_type == 'symbol']

ggplot(practice_data[stim_type == 'symbol'], aes(x=stim_val, y = real_prep_time)) + 
  geom_point() + 
  theme(axis.text.x=element_text(size=20))

ggplot(practice_data[correct & real_prep_time < 1], 
       aes(x = real_prep_time, y = stim_val, fill = stim_val)) + 
  geom_density_ridges(alpha=0.6, scale=5, rel_min_height=0.03, from=0, to=1)

practice_data[, dist_away := dist_from_last(proposed_choice), by = c('block', 'subject')]

ggplot(practice_data[!is.na(dist_away) & dist_away < 30 & block < 10], 
       aes(x = dist_away, y = as.numeric(correct), fill = factor(block))) + 
  stat_summary(fun.y = mean, geom = 'line', na.rm = TRUE) + 
  facet_wrap(~block) +
  coord_cartesian(ylim = c(0.75, 1))