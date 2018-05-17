from psychopy import visual
from psychopy import event
from time import sleep
win = visual.Window((1200,800), screen=1)
my_text = visual.TextStim(win, text ='\u16A6', 
                         height=0.5, units='norm', pos=(0,0), font='FreeMono')
my_text.draw()
win.flip()

event.waitKeys()

win.close()