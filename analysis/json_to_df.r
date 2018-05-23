library(RJSONIO)

subject_id = '001'

# list all blocks (subfolders of the top-level subject folder)
blocks <- dir(path = subject_id, full.names = TRUE)

trial_list <- list()
blk_list <- list()

for (i in 1:length(blocks)) {
  block_settings <- fromJSON(file.path(blocks[i], 'block_settings.json'))
  # note: there's a "practice" flag in block_settings, which we could use
  # to differentiate practice & not
  trials <- list.files(blocks[i], pattern = 'trial*')
  if (length(trials) > 0) { # if we have any data at all (once we're running people,
                            # should be every time)
    for (j in 1:length(trials)) { # loop through trials
      trial <- fromJSON(file.path(blocks[i], trials[j]), nullValue = NA)
      trial$rts <- NULL # remove the element from list
      trial$presses <- NULL
      trial_list[[j]] <- data.frame(trial)
    }
  }
  block <- do.call(rbind, trial_list) # data.table::rbindlist is faster
  block$block <- i # fill in a block number (one based off the datetime may be better,
                           # especially if we span multiple days)
  
  # you can plug in block_settings here (e.g. n_choices, image, seed,...)
  # subject number is also encoded in block_settings
  blk_list[[i]] <- block
}

dat <- do.call(rbind, blk_list)

# subject-level settings here (handedness? age?)
dat$subject <- subject_id
