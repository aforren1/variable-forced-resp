from datetime import datetime
import pickle

import yaml
import numpy as np

from forced_impl import ForcedResp
from generators import CriterionGen, UniformGen
from practice_impl import Practice
from psychopy import core, gui
from psychopy import event

if __name__ == '__main__':
    # bug: note that datatype seems funky after running through the GUI
    settings = {'root': 'data', 'subject': '001', 'fullscreen': False,
                'min_rt': 0.2, 'max_rt': 0.6, 'n_choices': 10,
                # formerly image
                'stim_type': ['hand', 'letter', 'symbol'],
                'exp_type': ['practice', 'criterion', 'probe'],
                'remap': False,
                'trials_per_stim': 10} # number of repeats per stimulus, e.g. this would result in 100 total trials

    try:
        with open('settings.pkl', 'rb') as f:
            potential_settings = pickle.load(f)
            # only use saved settings if all the keys match
            if potential_settings.keys() == settings.keys():
                settings = potential_settings
                settings['exp_type'] = ['practice', 'criterion', 'probe']
                settings['stim_type'] = ['hand', 'letter', 'symbol']
    except FileNotFoundError:
        pass

    dialog = gui.DlgFromDict(dictionary=settings, title='Experiment')
    if not dialog.OK:
        core.quit()
    # save the settings
    with open('settings.pkl', 'wb') as f:
        pickle.dump(settings, f)

    with open('static_settings.yml', 'r') as f:
        static_settings = yaml.load(f)

    if settings['exp_type'] == 'practice':
        gen = UniformGen(min_rt=float(settings['min_rt']),
                         max_rt=float(settings['max_rt']),
                         n_choices=int(settings['n_choices']),
                         seed=int(datetime.strftime(datetime.now(), '%H%M%S')),
                         trials_per_stim=int(settings['trials_per_stim']))
        Exp = Practice
    elif settings['exp_type'] == 'criterion':
        gen = CriterionGen(n_choices=int(settings['n_choices']), 
                           seed=int(datetime.strftime(datetime.now(), '%H%M%S')))
        Exp = Practice
    else:
        gen = UniformGen(min_rt=float(settings['min_rt']),
                         max_rt=float(settings['max_rt']),
                         n_choices=int(settings['n_choices']),
                         seed=int(datetime.strftime(datetime.now(), '%H%M%S')),
                         trials_per_stim=int(settings['trials_per_stim']))
        Exp = ForcedResp
    
    experiment = Exp(settings=settings, generator=gen,
                     static_settings=static_settings)

    with experiment.device:
        while experiment.state != 'cleanup':
            experiment.input()
            experiment.draw_input()
            experiment.step()
            experiment.win.flip()
            if event.getKeys(['esc', 'escape']):
                experiment.to_cleanup()
    core.quit()
