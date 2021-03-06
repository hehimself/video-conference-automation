a = 12
b = 0
c = 0

def test():
    b = 2
    return b

for attempt in range(2):
    try:
        c = a / b
        print(c)
    except ZeroDivisionError:
        b = test()
    else:
        break
else:
    print("Problem nicht gelöst")
b= 0
for attempt in range(2):
    try:
        c = a / b
        print(c)
    except ZeroDivisionError:
        b = test()
    else:
        break
else:
    print("Problem nicht gelöst")

# # import playsound
# # from threading import Thread
# import sys
# import time
# import threading
# import progressbar
# from termcolor import colored

# print(colored("VIDEO CONFERENCE AUTOMATION", "green", attrs=['bold']))

# def the_process_function():
#     try:
#         pass
#     except:
#         pass

    
    
# def animated_loading():
#     chars = ["   ",".  ",".. ", "..."]
#     for char in chars:
#         sys.stdout.write('\r'+'loading serial'+char+'  ')
#         time.sleep(.1)
#         sys.stdout.flush()

# the_process = threading.Thread(name='process', target=the_process_function)
# the_process.start()

# while the_process.isAlive():
#     animated_loading()
#     sys.stdout.write('\r'+'loading serial finished              \n')


# # def up():
# #     # My terminal breaks if we don't flush after the escape-code
# #     sys.stdout.write('\x1b[1A')
# #     sys.stdout.flush()

# # def down():
# #     # I could use '\x1b[1B' here, but newline is faster and easier
# #     sys.stdout.write('\n')
# #     sys.stdout.flush()

# # # Total bar is at the bottom. Move down to draw it
# # down()
# # total = progressbar.ProgressBar(maxval=50)
# # total.start()

# # for i in range(1,51):
# #     # Move back up to prepare for sub-bar
# #     up()

# #     # I make a new sub-bar for every iteration, thinking it could be things
# #     # like "File progress", with total being total file progress.
# #     sub = progressbar.ProgressBar(maxval=50)
# #     sub.start()
# #     for y in range(51):
# #         sub.update(y)
# #         time.sleep(0.005)
# #     sub.finish()

# #     # Update total - The sub-bar printed a newline on finish, so we already
# #     # have focus on it
# #     total.update(i)
# # total.finish()

# # # import progressbar

# # # bar = ChargingBar('Processing', max=100)
# # # for i in range(20):
# # #     # Do some work
# # #     time.sleep(.1)
# # #     bar.update(20)
# # # # bar.finish()
# # # #bar = progressbar.ProgressBar(max_value=progressbar.UnknownLength)
# # # # for i in range(10):
# # # #     time.sleep(0.1)
# # # #     bar.update(i)

# # # bar = progressbar.ProgressBar(max_value=progressbar.UnknownLength)
# # # for i in range(20):
# # #     time.sleep(0.1)
# # #     bar.update(i)

# # # for i in progressbar.progressbar(range(100), redirect_stdout=True):
# # #     print('Some text', i)
# # #     time.sleep(0.1)
# # '''Sound Test'''
# # # def sound():
# # #     playsound.playsound("jarvis.mp3")

# # # T = Thread(target=sound) # create thread
# # # T.start()
# # # print("jo")

# # '''hue Berechnung PICO'''
# # # # for i in range(0, 256, 10):
    
# # # #     print(i)

# # # # hue_offset = 0
# # # # forever:
# # # #     for every key on the keyboard:
# # # #         current_key_hue = normal_key_hue + hue_offset
# # # #         colour = make_colour_from(current_key_hue)
# # # #         set_colour(key, colour)
# # # #     apply_changes()

# # # #     hue_offset += hue_increment_value
# # # #     hue_offset %= max_hue

# # # #     delay()
# # # # colour = colorsys.hsv_to_rgb(x/10, 1.0, 255.0)
# # # # for x in range(4):
# # # #     for y in range(4):

# # # #         key_animation = keypad[x,y]
# # # #         key_animation.color = (0,i,0)

# # # import math
# # # import time

# # # spacing = 360.0 / 16.0
# # # hue = 0

# # # def hsv_to_rgb(h, s, v):
# # #     i = math.floor(h*6)
# # #     f = h*6 - i
# # #     p = v * (1-s)
# # #     q = v * (1-f*s)
# # #     t = v * (1-(1-f)*s)

# # #     r, g, b = [
# # #         (v, t, p),
# # #         (q, v, p),
# # #         (p, v, t),
# # #         (p, q, v),
# # #         (t, p, v),
# # #         (v, p, q),
# # #     ][int(i%6)]
# # #     return r, g, b

# # # while True:
# # #     hue = int(time.time() * 100) % 360
# # #     for x in range(4):
# # #         for y in range(4):
# # #             offset = x * spacing
# # #             h = ((hue + offset) % 360) / 360.0
# # #             r, g, b = [int(c * 255) for c in hsv_to_rgb(h, 1.0, 1.0)]
# # #             print(r , g, b)
# # #     time.sleep(0.001)

# # # for x in range(rgbmatrix5x5.width):
# # #         for y in range(rgbmatrix5x5.height):
# # #             hue = int(time.time() * 100) % 360
# # #             offset = (x * y) / 25.0 * spacing
# # #             h = ((hue + offset) % 360) / 360.0
# # #             r, g, b = [int(c * 255) for c in colorsys.hsv_to_rgb(h, 1.0, 1.0)]
# # #             rgbmatrix5x5.set_pixel(x, y, r, g, b)