import itertools
import ujson as json
import os
from datetime import datetime
from pprint import PrettyPrinter

import numpy as np
from psychopy import core, logging, sound, visual
import sounddevice as sd
import soundfile as sf

from practice_decl import StateMachine
from toon.input import MultiprocessInput as MpI
from toon.input.clock import mono_clock
from toon.input.keyboard import Keyboard

logging.setDefaultClock(mono_clock)
logging.console.setLevel(logging.ERROR)
if os.name == 'nt':
    sound.setDevice('ASIO4ALL v2')

pp = PrettyPrinter()

class Practice(StateMachine):
    def __init__(self, settings=None, generator=None, static_settings=None):
        super(Practice, self).__init__()
        self.settings = settings
        self.trial_generator = generator
        self.static_settings = static_settings

        self.global_clock = mono_clock
        self.feedback_timer = core.CountdownTimer()  # feedback duration
        self.post_timer = core.CountdownTimer()  # intertrial pause
        # how long key must be released before allowing continue
        self.release_timer = core.CountdownTimer()

        self.subject_rng = np.random.RandomState(seed=int(self.settings['subject']))

        self.setup_data()
        self.setup_window()
        self.setup_visuals()
        self.setup_input()
        self.setup_audio()

        self.frame_period = self.win.monitorFramePeriod
        self.this_trial_choice = None
        self.this_trial_rt = None
        self.trial_start = None
        self.first_press = None
        self.first_rt = None
        self.trial_counter = 0
        self.any_pressed = False
        self.already_released = False
        self.stim_onset = None
        self.t_feedback = 0
        self.valid_presses = []
        self.pause_presses = []

    def setup_data(self):
        # figure out the subject-specific remaps
        all_switch_hands = list(itertools.product(range(0, 5), range(5, 10)))
        homologous = [(0, 9), (1, 8), (2, 7), (3, 6), (4, 5)]
        heterologous = all_switch_hands.copy()
        for i in heterologous:
            if i in homologous:
                heterologous.remove(i)
        same_hand_l = list(itertools.product(
            list(range(0, 5)), list(range(0, 5))))
        same_hand_l = [(i, j) for i, j in same_hand_l if i != j]
        same_hand_r = [(i + 5, j + 5) for i, j in same_hand_l]
        same_hand = same_hand_l + same_hand_r

        # choose one homologous, heterologous, same hand
        self.subject_rng = np.random.RandomState(seed=int(self.settings['subject']))
        hom_choice = self.subject_rng.choice(len(homologous))
        hom_pair = homologous[hom_choice]
        # make sure we can't pick an already engaged finger
        het_subset = [i for i in heterologous 
                        if not set(i).intersection(hom_pair)]
        het_choice = self.subject_rng.choice(len(het_subset))
        het_pair = het_subset[het_choice]
        same_hand_subset = [i for i in same_hand 
                                if not set(i).intersection(hom_pair) and 
                                    not set(i).intersection(het_pair)]
        same_hand_choice = self.subject_rng.choice(len(same_hand_subset))
        same_hand_pair = same_hand_subset[same_hand_choice]

        self.all_swaps = [hom_pair] + [het_pair] + [same_hand_pair]
        self.settings.update({'swap_pairs': self.all_swaps})

        #
        self.start_datetime = datetime.now().strftime('%y%m%d_%H%M%S')
        self.data_path = os.path.join(
            self.static_settings['root'], self.settings['subject'], self.start_datetime)
        self.settings.update({'datetime': self.start_datetime})

        # log from psychopy (to log here, call something like `logging.warning('bad thing')`)
        if not os.path.exists(self.data_path):
            os.makedirs(self.data_path)
        self.logfile = logging.LogFile(os.path.join(
            self.data_path, 'psychopy_log.log'), filemode='w', level=logging.INFO)

        # log block-level settings
        with open(os.path.join(self.data_path, 'block_settings.json'), 'w') as f:
            json.dump(self.settings, f)
        with open(os.path.join(self.data_path, 'static_block_settings.json'), 'w') as f:
            json.dump(self.static_settings, f)

        # trial-specific data (will be serialized via json.dump)
        self.trial_data = {'index': None, 'real_prep_time': None,
                           'proposed_choice': None, 'real_choice': None, 'correct': None,
                           'datetime': None, 'presses': [], 'rts': [], 'will_remap': None,
                           'is_remapped': None, 'remapped_from': None,
                           'stim_val': None}

    def setup_window(self):
        self.win = visual.Window(size=(800, 800), pos=(0, 0), fullscr=self.static_settings['fullscreen'],
                                 screen=1, units='height', allowGUI=False, colorSpace='rgb',
                                 color=-1.0)
        self.win.recordFrameIntervals = True
        # bump up the number of dropped frames reported
        visual.window.reportNDroppedFrames = 50

    def setup_visuals(self):
        self.targets = list()
        # all possible targets
        tmp = list(self.static_settings['symbol_options'])

        # compute per-person mapping
        self.subject_rng = np.random.RandomState(seed=int(self.settings['subject']))
        self.subject_rng.shuffle(tmp)
        tmp = ''.join(tmp)  # convert from list to string
        self.settings.update({'reordered_symbols': tmp})

        tmp = tmp[:int(self.static_settings['n_choices'])]
        if self.settings['stim_type'] == 'symbol':
            for i in tmp:
                self.targets.append(visual.TextStim(
                    self.win, i, height=0.25, autoLog=True, font='FreeMono', name='stim ' + i))
        elif self.settings['stim_type'] == 'letter':
            for i in list(self.static_settings['key_options']):
                self.targets.append(visual.TextStim(
                    self.win, i, height=0.25, autoLog=True, font='FreeMono', name='stim ' + i))
        elif self.settings['stim_type'] == 'hand':
            right_hand = visual.ImageStim(self.win, image='media/hand.png', size=(0.3, 0.3),
                                          pos=(0.14, 0))
            left_hand = visual.ImageStim(self.win, image='media/hand.png', size=(0.3, 0.3),
                                         pos=(-0.14, 0), flipHoriz=True)
            self.background = visual.BufferImageStim(self.win, stim=[left_hand, right_hand])
            # pinky, ring, middle, index, thumb
            pos_l = [[-0.255, 0.0375], [-0.2075, 0.08875],
                     [-0.1575, 0.1125], [-0.095, 0.09], [-0.03, -0.0075]]
            pos_r = [[-x, y] for x, y in pos_l]
            pos_r.reverse()
            pos_l.extend(pos_r)
            pos_l = pos_l[:int(self.static_settings['n_choices'])]

            self.targets = [visual.Circle(self.win, fillColor=(1, 1, 1), pos=x,
                                          size=0.03, opacity=1.0, name='stim %d' % c)
                            for c, x in enumerate(pos_l)]
        else:
            raise ValueError('Unknown stimulus option...')

        if self.settings['remap']:
            # remap heterologous, homologous, and same-finger pairs?
            # swap the stimuli
            for i, j in self.all_swaps:
                self.targets[j], self.targets[i] = self.targets[i], self.targets[j]
            
        # push feedback
        self.push_feedback = visual.Rect(
            self.win, width=0.6, height=0.6, lineWidth=3, name='push_feedback', autoLog=False)

        # text
        self.instruction_text = visual.TextStim(self.win, text='Press a key to start.', pos=(0, 0),
                                                units='norm', color=(1, 1, 1), height=0.1,
                                                alignHoriz='center', alignVert='center', name='wait_text',
                                                autoLog=False, wrapWidth=2)
        self.instruction_text.autoDraw = True

        self.pause_text = visual.TextStim(self.win, text=u'Take a break!', pos=(0, 0.8),
                                           units='norm', color=(1, 1, 1), height=0.1,
                                           alignHoriz='center', alignVert='center', autoLog=True, name='pause_text')
        self.pause_text2 = visual.TextStim(self.win, text=u'Press ten times to continue.', pos=(0, 0.7),
                                           units='norm', color=(1, 1, 1), height=0.1,
                                           alignHoriz='center', alignVert='center', autoLog=True, name='pause_text')

    def setup_audio(self):
        if os.name == 'nt':
            self.coin = sound.Sound('sounds/coin.wav', stereo=True)
        else:
            sd.default.latency = 0.01
            sd.default.blocksize = 32
            data, self.coin_fs = sf.read('sounds/coin.wav')
            self.coin_data = np.transpose(np.vstack((data, data)))
        self._play_reward()

    def _play_reward(self):
        if os.name == 'nt':
            self.coin.play()
        else:
            sd.play(self.coin_data, self.coin_fs)

    def setup_input(self):
        keys = list(self.static_settings['key_options'])
        self.keys = keys[:int(self.static_settings['n_choices'])]
        self.device = MpI(Keyboard, keys=keys, clock=self.global_clock.getTime)
        self.keyboard_state = [False] * len(keys)

    # State-specific methods
    # wait state
    # conditions
    def wait_for_press(self):
        return self.any_pressed

    # after
    def remove_instruction_text(self):
        self.instruction_text.autoDraw = False

    def add_fix_n_feedback(self):
        # always keep hands on if we're doing the hand stimuli
        if self.settings['stim_type'] == 'hand':
            self.background.autoDraw = True
        self.push_feedback.autoDraw = True

    # pretrial state
    # conditions
    def wait_for_release(self):
        tmp = not self.any_pressed
        if tmp and not self.already_released:
            self.release_timer.reset(0.3)
            self.already_released = True
        return tmp

    def wait_n_ms_after_release(self):
        return self.release_timer.getTime() <= 0

    # after
    def get_next_rt_n_resp(self):
        self.this_trial_rt, self.this_trial_choice = self.trial_generator.next()

    def sched_record_trial_start(self):
        self.win.callOnFlip(self._get_trial_start)

    def _get_trial_start(self):
        self.trial_start = self.win.lastFrameT
        logging.info('Trial %d start: %f' %
                     (self.trial_counter, self.trial_start))

    def first_press_reset(self):
        self.first_press = None
        self.first_rt = None
        self.trial_data['presses'] = []
        self.trial_data['rts'] = []
        self.valid_presses = []

    def add_stim(self):
        self.targets[int(self.this_trial_choice)].autoDraw = True
        self.win.callOnFlip(self.record_stim_time)

    # enter_trial state
    # conditions
    def wait_for_trial_press(self):
        if self.valid_presses:
            return True
        return False

    def record_stim_time(self):
        self.stim_onset = self.win.lastFrameT - self.trial_start
        logging.exp('Drew image %d at %f' %
                    (int(self.this_trial_choice), self.stim_onset))

    # after
    def add_feedback(self):
        # draw feedback (text, change colors...)
        # if not too slow, red or green stimulus (incorrect or correct)
        # if too slow, show text
        if self.valid_presses:
            correct = self.valid_presses[-1] == int(self.this_trial_choice)
            if correct:
                if self.settings['stim_type'] != 'hand':
                    self.targets[int(self.this_trial_choice)].color = [-1, 1, -1]
                else:
                    self.targets[int(self.this_trial_choice)].fillColor = [-1, 1, -1]
                self._play_reward()
                self.t_feedback = 0.3
            else:
                if self.settings['stim_type'] != 'hand':
                    self.targets[int(self.this_trial_choice)].color = [1, -1, -1]
                else:
                    self.targets[int(self.this_trial_choice)].fillColor = [1, -1, -1]
                self.t_feedback = 1.0

    def start_feedback_timer(self):
        self.feedback_timer.reset(self.t_feedback)

    # feedback state
    # conditions
    def feedback_timer_passed(self):
        return self.feedback_timer.getTime() - self.frame_period <= 0

    def is_choice_correct(self):
        return self.t_feedback < 0.5
        # return self.trial_data['presses'][-1] == self.this_trial_choice

    def is_choice_incorrect(self):
        was_incorrect = self.t_feedback > 0.5
        if was_incorrect:
            self.valid_presses = []
        return was_incorrect

    # after
    def remove_stim(self):
        self.targets[int(self.this_trial_choice)].autoDraw = False

    def remove_feedback(self):
        if self.settings['stim_type'] != 'hand':
            self.targets[int(self.this_trial_choice)].color = [1, 1, 1]
        else:
            self.targets[int(self.this_trial_choice)].fillColor = [1, 1, 1]
        self.valid_presses = []

    def start_post_timer(self):
        self.post_timer.reset(0.2)

    def record_data(self):
        now = datetime.now().strftime('%y%m%d_%H%M%S%f')
        self.trial_data['index'] = self.trial_counter
        self.trial_data['real_prep_time'] = float(
            self.first_rt - self.stim_onset) if self.first_rt else None
        self.trial_data['proposed_choice'] = int(
            self.this_trial_choice) if self.this_trial_choice is not None else None
        self.trial_data['real_choice'] = int(
            self.first_press) if self.first_press is not None else None
        self.trial_data['correct'] = bool(
            self.first_press == int(self.this_trial_choice)) if self.first_press is not None else False
        self.trial_data['datetime'] = now
        self.trial_data['presses'] = list(self.trial_data['presses'])
        self.trial_data['rts'] = [x - self.stim_onset for x in self.trial_data['rts']]
        # remapping things
        self.trial_data['will_remap'] = any(self.trial_data['proposed_choice'] in r for r in self.all_swaps)
        self.trial_data['is_remapped'] = self.trial_data['will_remap'] and self.settings['remap']
        if self.trial_data['is_remapped']:
            pair = [r for r in self.all_swaps if self.this_trial_choice in r][0] # should only be one list
            pair = list(pair)
            pair.remove(self.this_trial_choice)
        self.trial_data['remapped_from'] = int(pair[0]) if self.trial_data['is_remapped'] else None
        if self.settings['stim_type'] == 'hand':
            x = str(self.this_trial_choice)
        else:
            x = self.targets[int(self.this_trial_choice)].text
        #elif self.settings['stim_type'] == 'symbol':
        #    x = hex(ord(self.targets[int(self.this_trial_choice)].text))
        self.trial_data['stim_val'] = x
        #pp.pprint(self.trial_data)
        trial_name = 'trial' + str(self.trial_counter) + '_summary.json'
        with open(os.path.join(self.data_path, trial_name), 'w') as f:
            json.dump(self.trial_data, f)
        for k in self.trial_data:
            self.trial_data[k] = None
        self.trial_data['presses'] = []
        self.trial_data['rts'] = []

    def increment_trial_counter(self):
        self.trial_counter += 1

    def update_rt_gen(self):
        self.trial_generator.update(self.first_press, self.first_rt)

    def reset_release_flag(self):
        self.already_released = False

    # post_trial state
    # conditions
    def stopping_conditions(self):
        return self.trial_generator.should_terminate()

    # conditions, part 2
    def post_timer_passed(self):
        return self.post_timer.getTime() - self.frame_period <= 0

    # conditions, part 3
    def mult_of_100_passed(self):
        return self.trial_counter % 100 == 0
    
    def reset_pause_press_list(self):
        self.pause_presses = []
    
    def ten_keys_pressed(self):
        lpp = len(self.pause_presses)
        self.pause_text2.text = 'Press %d times to continue.' % (10 - lpp)
        return lpp >= 10

    def draw_pause_text(self):
        self.pause_text.autoDraw = True
        self.pause_text2.autoDraw = True

    def rm_pause_text(self):
        self.pause_text.autoDraw = False
        self.pause_text2.autoDraw = False

    def input(self):
        timestamp, data = self.device.read()
        if timestamp is not None:
            for i, j in zip(data[0], data[1]):
                self.keyboard_state[j[0]] = i[0]
            self.any_pressed = any(self.keyboard_state)
            if not self.first_press and self.any_pressed and self.trial_start:
                self.first_press = data[1][0][0]
                self.first_rt = (timestamp - self.trial_start)[0]
            if self.trial_start:
                for i in range(len(data[0][0])):
                    if data[0][0][i]:
                        self.trial_data['presses'].append(int(data[1][0][i]))
                        self.trial_data['rts'].append(
                            float(timestamp[i] - self.trial_start))
                        self.valid_presses.append(int(data[1][0][i]))
            if self.state == 'wait_till_10_pressed':
                for i in range(len(data[0][0])):
                    if data[0][0][i]:
                        self.pause_presses.append(int(data[1][0][i]))

    def draw_input(self):
        self.push_feedback.lineColor = [0, 0, 0] if self.any_pressed else [1, 1, 1]
