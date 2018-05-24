library(ggplot2)
source('preprocess.r')
source('misc.r')

all_data <- preprocess()

probe_data <- all_data[['probe_data']]

probe_data <- probe_data[stim_type == 'symbol']
probe_data[, slide_correct := slider(x = real_prep_time, y = correct)]
probe_data[, slide_stim := slider(x = real_prep_time, y = correct), by = c('stim_val', 'subject')]
probe_data[, slide_finger := slider(x = real_prep_time, y = correct), by = c('proposed_choice', 'subject')]



ggplot(probe_data, aes(x = real_prep_time, y = slide_stim, colour = factor(proposed_choice))) + 
  geom_line(size=1) + 
  facet_wrap(stim_val~subject)

ggplot(probe_data, aes(x = real_prep_time, y = slide_finger, colour = stim_val)) +
  geom_line(size = 1) +
  facet_wrap(proposed_choice ~ subject)
