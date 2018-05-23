library(ggplot2)
source('preprocess.r')
source('misc.r')

all_data <- preprocess()

probe_data <- all_data[['probe_data']]

probe_data <- probe_data[stim_type == 'symbol']
probe_data[, slide_correct := slider(x = real_prep_time, y = correct)]
probe_data[, slide_correct_sym := slider(x = real_prep_time, y = correct), by = c('proposed_choice')]

ggplot(probe_data, aes(x = real_prep_time, y = slide_correct_sym, colour = factor(proposed_choice))) + 
  geom_line() + 
  facet_wrap(~proposed_choice)
