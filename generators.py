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
    def __init__(self, n_choices=2, seed=None, interval=1/60, **kwargs):
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
        self.count = 0

    def update(self, choice, actual_pt):
        """Store the choice and preparation time.
        Call after response has been made
        """
        self.choices.append(choice)
        self.prep_times.append(actual_pt)
        self.corrects.append(choice == self.current_choice)
        self.req_choices.append(self.current_choice)
        self.req_prep_times.append(self.current_prep_time)
        self.count += 1


class UniformGen(TrialGenerator):
    def __init__(self, min_rt=0.1, max_rt=0.5, trials_per_stim=25, **kwargs):
        super(UniformGen, self).__init__(**kwargs)
        self.max_trials = trials_per_stim * self.n_choices
        # convert to list for pop?
        self.options = np.arange(min_rt, max_rt, self.interval)
        self.total_choices = np.repeat(
            range(self.n_choices), int(trials_per_stim)).astype('int')
        self.rng.shuffle(self.total_choices)
        self.prop_rts = self.rng.choice(self.options, size=self.max_trials)

    def next(self):
        return (self.prop_rts[self.count], self.total_choices[self.count])

    def should_terminate(self):
        return self.count >= self.max_trials



class CriterionGen(TrialGenerator):
    def __init__(self, percentage=0.8, out_of=5, **kwargs):
        # percentage = percentage of correct responses
        # out_of = number back to check
        super(CriterionGen, self).__init__(**kwargs)
        self.percentage = percentage
        self.out_of = out_of

    def next(self):
        self.current_choice = self.rng.randint(self.n_choices)
        self.current_prep_time = 0
        return (self.current_prep_time, self.current_choice)

    def should_terminate(self):
        for i in range(self.n_choices):
            if i in self.req_choices:
                # indices of *all* of the points for the current choice
                indices = [ii for ii, jj in enumerate(self.req_choices) if jj == i]
                # get all the corrects
                subset_correct = [self.corrects[a] for a in indices]
                out_of_last_n_correct = sum(subset_correct[-self.out_of:])/self.out_of
                if out_of_last_n_correct >= self.percentage:
                    continue
                else:
                    return False
            else:
                return False
        # if we make it this far, all choices have continued
        return True
