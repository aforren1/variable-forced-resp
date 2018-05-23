library(ggplot2)
source('preprocess.r')
source('misc.r')

all_data <- preprocess()

probe_data <- all_data[['probe_data']]

