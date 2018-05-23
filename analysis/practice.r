library(ggplot2)
source('preprocess.r')
source('misc.r')

all_data <- preprocess()

practice_data <- all_data[['practice_data']]

ggplot(practice_data[stim_type == 'symbol'], aes(x=stim_val, y = real_prep_time)) + 
  geom_point() + 
  theme(axis.text.x=element_text(size=20))
