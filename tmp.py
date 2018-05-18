from psychopy import visual
from psychopy import event
from time import sleep
win = visual.Window((1200,800), screen=1, units='height')
#my_text = visual.TextStim(win, text ='\u16A0\u16a2\u16a3\u16a6\u16cb\u16aC\u16B3\u16BB\u16BC\u16C7', 
#                         height=0.5, units='norm', pos=(0,0), font='FreeMono')
#my_text.draw()

mouse = event.Mouse()

right_hand = visual.ImageStim(win, image='media/hand.png', size=(0.3, 0.3), 
                                pos=(0.14, 0))
left_hand = visual.ImageStim(win, image='media/hand.png', size=(0.3, 0.3), 
                                pos=(-0.14, 0), flipHoriz=True)
both = visual.BufferImageStim(win, stim=[left_hand, right_hand])
both.autoDraw = True

pos_l = [[-0.255, 0.0375], [-0.2075, 0.08875], [-0.1575, 0.1125], [-0.095, 0.09], [-0.03, -0.0075]]
pos_r = [[-x, y] for x, y in pos_l]
pos_r.reverse()
pos_l.extend(pos_r)

targets = [visual.Circle(win, fillColor=(1, 1, 1), pos=x, 
                            size=0.03, opacity=1.0, autoDraw=True) 
                for x in pos_l]
win.flip()

while not event.getKeys():
    print(mouse.getPos())

win.close()