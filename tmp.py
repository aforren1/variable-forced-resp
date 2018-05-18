from psychopy import visual
from psychopy import event
from time import sleep
win = visual.Window((1200,800), screen=1, units='height')
mouse = event.Mouse()
my_text = visual.TextStim(win, text ='\u16A0\u16a2\u16a3\u16a6\u16cb\u16aC\u16B3\u16BB\u16BC\u16C7', 
                         height=0.5, units='norm', pos=(0,0), font='FreeMono')
my_text.draw()

win.flip()

while not event.getKeys():
    print(mouse.getPos())

win.close()