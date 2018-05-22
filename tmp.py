from psychopy import visual
from psychopy import event
from time import sleep
win = visual.Window((1200,800), screen=1, units='height')
mouse = event.Mouse()
my_text = visual.TextStim(win, text=u'Take a break!', pos=(0, 0.8),
                                    units='norm', color=(1, 1, 1), height=0.1,
                                    alignHoriz='center', alignVert='center', autoLog=True, name='pause_text')

my_text2 = visual.TextStim(win, text=u'Press 10 times to continue.', pos=(0, 0.7),
                                    units='norm', color=(1, 1, 1), height=0.1,
                                    alignHoriz='center', alignVert='center', autoLog=True, name=' ')
my_text.draw()
my_text2.draw()
push_feedback = visual.Rect(win, width=0.6, height=0.6, lineWidth=3, name='push_feedback', autoLog=False)
push_feedback.draw()
win.flip()

while not event.getKeys():
    print(mouse.getPos())

win.close()