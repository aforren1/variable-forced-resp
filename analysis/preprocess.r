library(data.table)
library(RJSONIO)

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
    for (j in 1:length(blocks)) {
        trial_list <- list()
      
        block_settings <- fromJSON(file.path(blocks[j], 'block_settings.json'))
        trials <- list.files(blocks[j], pattern = 'trial*')
        if (length(trials) <= 0) { 
            warning(paste0('block ' + str(j) + ' subject ' + block_settings$subject))
            break
        }

        for (k in 1:length(trials)) {
            trial <- fromJSON(file.path(blocks[j], trials[k]), nullValue = NA)
            trial$rts <- NULL
            trial$presses <- NULL
            trial$datetime <- strptime(trial$datetime, '%y%m%d_%H%M%S')
            trial_list[[k]] <- data.frame(trial)
        }

        block <- rbindlist(trial_list)
        block$block <- j
        block$remap <- block_settings$remap
        block$subject <- block_settings$subject
        block$stim_type <- block_settings$stim_type
        block$exp_type <- block_settings$exp_type

        if (block_settings$exp_type == 'practice') { block_list_practice[[j]] = block }
        if (block_settings$exp_type == 'probe') { block_list_probe[[j]] = block }
        if (block_settings$exp_type == 'criterion') { block_list_criterion[[j]] = block }
    }
    
    block_list_probe <- block_list_probe[-which(sapply(block_list_probe, is.null))]
    block_list_practice <- block_list_practice[-which(sapply(block_list_practice, is.null))]
    block_list_criterion <- block_list_criterion[-which(sapply(block_list_criterion, is.null))]
    
    subject_list_probe[[i]] <- rbindlist(block_list_probe)
    subject_list_practice[[i]] <- rbindlist(block_list_practice)
    subject_list_criterion[[i]] <- rbindlist(block_list_criterion)
}

#subject_list_probe <- subject_list_probe[-which(sapply(subject_list_probe, is.null))]
#subject_list_practice <- subject_list_practice[-which(sapply(subject_list_practice, is.null))]
#subject_list_criterion <- subject_list_criterion[-which(sapply(subject_list_criterion, is.null))]

probe_data <- rbindlist(subject_list_probe)
practice_data <- rbindlist(subject_list_practice)
criterion_data <- rbindlist(subject_list_criterion)

