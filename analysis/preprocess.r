library(data.table)
#library(RJSONIO)
library(rjson)

options(datatable.print.nrows = 30)

preprocess <- function() {
  subjects <- dir('../data/', full.names = TRUE)
  
  subject_list_practice <- list()
  subject_list_criterion <- list()
  subject_list_probe <- list()
  
  # iterate per subject
  for (i in 1:length(subjects)) {
    blocks <- dir(path = subjects[i], full.names = TRUE)
    
    block_list_practice <- list()
    block_list_criterion <- list()
    block_list_probe <- list()
    # iterate per block within subject
    block_counter <- 1
    for (j in 1:length(blocks)) {
      trial_list <- list()
      
      block_settings <- fromJSON(file = file.path(blocks[j], 'block_settings.json'))
      trials <- list.files(blocks[j], pattern = 'trial*')
      if (length(trials) <= 0) {
        warning(paste0('block '+str(j) + ' subject '+block_settings$subject))
        break
      }
      
      for (k in 1:length(trials)) {
        trial <- fromJSON(file = file.path(blocks[j], trials[k]))
        trial[sapply(trial, is.null)] <- NA
        trial$rts <- NULL
        trial$presses <- NULL
        trial$datetime <-
          strptime(trial$datetime, '%y%m%d_%H%M%S')
        trial_list[[k]] <- data.frame(trial, stringsAsFactors = FALSE)
      }
      
      block <- do.call(rbind, trial_list)
      block$block <- block_counter
      block_counter <- block_counter + 1
      block$remap <- block_settings$remap
      block$subject <- block_settings$subject
      block$stim_type <- block_settings$stim_type
      block$exp_type <- block_settings$exp_type
      
      if (block_settings$exp_type == 'practice') {
        block_list_practice[[j]] = block
      }
      if (block_settings$exp_type == 'probe') {
        block_list_probe[[j]] = block
      }
      if (block_settings$exp_type == 'criterion') {
        block_list_criterion[[j]] = block
      }
    }
    
    block_list_probe <-
      block_list_probe[!sapply(block_list_probe, is.null)]
    block_list_practice <-
      block_list_practice[!sapply(block_list_practice, is.null)]
    block_list_criterion <-
      block_list_criterion[!sapply(block_list_criterion, is.null)]
    
    subject_list_probe[[i]] <- do.call(rbind,block_list_probe)
    subject_list_practice[[i]] <- do.call(rbind,block_list_practice)
    subject_list_criterion[[i]] <- do.call(rbind,block_list_criterion)
  }
  
  subject_list_probe <-
    subject_list_probe[!sapply(subject_list_probe, is.null)]
  subject_list_practice <-
    subject_list_practice[!sapply(subject_list_practice, is.null)]
  subject_list_criterion <-
    subject_list_criterion[!sapply(subject_list_criterion, is.null)]
  
  probe_data <- as.data.table(do.call(rbind,subject_list_probe))
  practice_data <- as.data.table(do.call(rbind,subject_list_practice))
  criterion_data <- as.data.table(do.call(rbind,subject_list_criterion))
  
  probe_data <- probe_data[order(datetime)]
  practice_data <- practice_data[order(datetime)]
  criterion_data <- criterion_data[order(datetime)]
  
  list(probe_data = probe_data, practice_data = practice_data, criterion_data = criterion_data)
  
}
