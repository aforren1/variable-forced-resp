import abc
import numpy as np

# Do we need to account for discretization of the image, 
# because a proposed prep time will (almost) never match up w/
# the screen refresh...
class TrialGenerator(abc.ABC):
    @abc.abstractmethod
    def next(self):
        """Generate the next choice/prep_time combo
        return (choice, prep_time) tuple
        """
        pass
    @abc.abstractmethod
    def should_terminate(self):
        """check termination conditions (trial count, % correct, ...)"""
        pass
    @abc.abstractmethod
    def __init__(self, n_choices=2, seed=None, interval=1/60):
        """Create the generator
        kwargs might be min_rt, max_rt, and other things to feed into next()
        Call random number generation things from self.rng!

        Interval is used to restrict the proposed RT steps
        """
        self.rng = np.random.RandomState(seed=seed)
        self.n_choices = n_choices
        self.interval = interval
        self.current_choice = None
        self.current_prep_time = None
        self.choices = list()
        self.prep_times = list()
        self.corrects = list()
        self.req_choices = list()
        self.req_prep_times = list()
    
    @abc.abstractmethod
    def update(self, choice, actual_pt):
        """Store the choice and preparation time.
        Call after response has been made
        """
        self.choices.append(choice)
        self.prep_times.append(actual_pt)
        self.corrects.append(choice == self.current_choice)
        self.req_choices.append(self.current_choice)
        self.req_prep_times.append(self.current_prep_time)

class UniformGen(TrialGenerator):
    def __init__(self, min_rt=0.1, max_rt=0.5, **kwargs):
        super(UniformGen, self).__init__(**kwargs)
        self.options = np.arange(min_rt, max_rt, self.interval) # convert to list for pop?
    
    def next(self):
        self.current_choice = self.rng.randint(self.n_choices)
        self.current_prep_time = self.rng.choice(self.options)
        return (self.current_prep_time, self.current_choice)
    
    def should_terminate(self):
        return len(self.choices) > 10
    
    def update(self, *args):
        super(UniformGen, self).update(*args)
