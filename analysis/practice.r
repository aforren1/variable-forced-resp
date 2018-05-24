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
