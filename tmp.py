from psychopy import visual
from psychopy import event
from time import sleep
win = visual.Window((1200,800), screen=1, units='height')
mouse = event.Mouse()
mouse.setExclusive(True)
right_hand = visual.ImageStim(win, image='media/hand.png', size=(0.3, 0.3),
                                          pos=(0.14, 0))
left_hand = visual.ImageStim(win, image='media/hand.png', size=(0.3, 0.3),
                                         pos=(-0.14, 0), flipHoriz=True)
background = visual.BufferImageStim(win, stim=[left_hand, right_hand])
background.units = 'height'
background.draw()
win.flip()

while not event.getKeys():
    tmp = mouse.getPressed()
    if any(tmp):
        print('clicked')
        background.thisScale += (1, -1)
        background.ori -= 0.1
    background.draw()
    win.flip()

win.close()