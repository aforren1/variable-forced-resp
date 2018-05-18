import pickle

import yaml

from forced_impl import ForcedResp
from generators import CriterionGen, UniformGen
from practice_impl import Practice
from psychopy import core, gui
from psychopy.event import Mouse

if __name__ == '__main__':
    # bug: note that datatype seems funky after running through the GUI
    settings = {'root': 'data', 'subject': '001', 'fullscreen': False,
                'min_rt': 0.2, 'max_rt': 0.6, 'seed': 1, 'n_choices': 10,
                # formerly image
                'stim_per_choice': 1, 'stim_type': ['hand', 'letter', 'symbol'],
                'exp_type': ['practice', 'criterion', 'probe']}

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

    gen = UniformGen(min_rt=float(settings['min_rt']),
                     max_rt=float(settings['max_rt']),
                     n_choices=int(settings['n_choices']),
                     seed=int(settings['seed']))

    with open('static_settings.yml', 'r') as f:
        static_settings = yaml.load(f)

    if settings['exp_type'] is 'practice':
        gen = UniformGen(min_rt=float(settings['min_rt']),
                         max_rt=float(settings['max_rt']),
                         n_choices=int(settings['n_choices']),
                         seed=int(settings['seed']))
        Exp = Practice
    elif settings['exp_type'] is 'criterion':
        gen = CriterionGen(n_choices=int(settings['n_choices']), 
                           seed=int(settings['seed']))
        Exp = Practice
    else:
        gen = UniformGen(min_rt=float(settings['min_rt']),
                         max_rt=float(settings['max_rt']),
                         n_choices=int(settings['n_choices']),
                         seed=int(settings['seed']))
        Exp = ForcedResp
    experiment = Exp(settings=settings, generator=gen,
                     static_settings=static_settings)

    mouse = Mouse(visible=False, win=experiment.win)
    with experiment.device:
        while experiment.state is not 'cleanup':
            experiment.input()
            experiment.draw_input()
            experiment.step()
            experiment.win.flip()
            if any(mouse.getPressed()):
                experiment.to_cleanup()
    core.quit()
