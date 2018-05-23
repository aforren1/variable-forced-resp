
library(ggplot2)
source('preprocess.r')
source('misc.r')

all_data <- preprocess()

criterion_data <- all_data[['criterion_data']]

# number of repeats per stimulus
print(criterion_data[, .N, by = c('proposed_choice')])