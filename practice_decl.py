from transitions import Machine


class StateMachine(Machine):
    def __init__(self):
        states = ['wait',
                  'pretrial',
                  'enter_trial',
                  'feedback',
                  'post_trial',
                  'wait_till_10_pressed',
                  'cleanup']

        transitions = [
            # show instructions, wait for any response to start
            {'source': 'wait',
             'trigger': 'step',
             'conditions': 'wait_for_press',
             'after': ['remove_instruction_text',
                       'add_fix_n_feedback'],
             'dest': 'pretrial'},
            # wait for keys to be released
            # compute the next reaction time, response pair
            # draw the stimulus
            {'source': 'pretrial',
             'trigger': 'step',
             'conditions': ['wait_for_release',
                            'wait_n_ms_after_release'],
             'after': ['get_next_rt_n_resp',
                       'sched_record_trial_start',
                       'first_press_reset',
                       'add_stim'],
             'dest': 'enter_trial'},

            {'source': 'enter_trial',
             'trigger': 'step',
             'conditions': 'wait_for_trial_press',
             'after': ['add_feedback',
                       'start_feedback_timer'],
             'dest': 'feedback'},

            # stop drawing feedback after some time
            {'source': 'feedback',
             'trigger': 'step',
             'conditions': ['feedback_timer_passed', 'is_choice_correct'],
             'after': ['remove_stim', 'remove_feedback',
                       'start_post_timer',
                       'record_data',
                       'increment_trial_counter',
                       'update_rt_gen',
                       'reset_release_flag'],
             'dest': 'post_trial'},
            # if choice was incorrect, loop back around to enter_trial
            {'source': 'feedback',
             'trigger': 'step',
             'conditions': ['feedback_timer_passed', 'is_choice_incorrect'],
             'after': 'remove_feedback',
             'dest': 'enter_trial'},
            
            # check if stopping conditions met
            {'source': 'post_trial',
             'trigger': 'step',
             'conditions': 'stopping_conditions',
             'dest': 'cleanup'},
            
            # check if we need to take a break
            {'source': 'post_trial',
             'trigger': 'step',
             'conditions': 'mult_of_100_passed',
             'after': ['reset_pause_press_list', 'draw_pause_text'],
             'dest': 'wait_till_10_pressed'},

            # if stopping not met, then wait for *any* press (if none during trial)
            # and wait for ITI as well
            {'source': 'post_trial',
             'trigger': 'step',
             'conditions': 'post_timer_passed',
             'dest': 'pretrial'},

            {'source': 'wait_till_10_pressed',
             'trigger': 'step',
             'conditions': 'ten_keys_pressed',
             'after': 'rm_pause_text',
             'dest': 'pretrial'}
        ]
        Machine.__init__(self, states=states, transitions=transitions,
                         initial=states[0])
