import playsound
from threading import Thread

def sound():
    playsound.playsound("jarvis.mp3")

T = Thread(target=sound) # create thread
T.start()
print("jo")
# # for i in range(0, 256, 10):
    
# #     print(i)

# # hue_offset = 0
# # forever:
# #     for every key on the keyboard:
# #         current_key_hue = normal_key_hue + hue_offset
# #         colour = make_colour_from(current_key_hue)
# #         set_colour(key, colour)
# #     apply_changes()

# #     hue_offset += hue_increment_value
# #     hue_offset %= max_hue

# #     delay()
# # colour = colorsys.hsv_to_rgb(x/10, 1.0, 255.0)
# # for x in range(4):
# #     for y in range(4):

# #         key_animation = keypad[x,y]
# #         key_animation.color = (0,i,0)

# import math
# import time

# spacing = 360.0 / 16.0
# hue = 0

# def hsv_to_rgb(h, s, v):
#     i = math.floor(h*6)
#     f = h*6 - i
#     p = v * (1-s)
#     q = v * (1-f*s)
#     t = v * (1-(1-f)*s)

#     r, g, b = [
#         (v, t, p),
#         (q, v, p),
#         (p, v, t),
#         (p, q, v),
#         (t, p, v),
#         (v, p, q),
#     ][int(i%6)]
#     return r, g, b

# while True:
#     hue = int(time.time() * 100) % 360
#     for x in range(4):
#         for y in range(4):
#             offset = x * spacing
#             h = ((hue + offset) % 360) / 360.0
#             r, g, b = [int(c * 255) for c in hsv_to_rgb(h, 1.0, 1.0)]
#             print(r , g, b)
#     time.sleep(0.001)

# for x in range(rgbmatrix5x5.width):
#         for y in range(rgbmatrix5x5.height):
#             hue = int(time.time() * 100) % 360
#             offset = (x * y) / 25.0 * spacing
#             h = ((hue + offset) % 360) / 360.0
#             r, g, b = [int(c * 255) for c in colorsys.hsv_to_rgb(h, 1.0, 1.0)]
#             rgbmatrix5x5.set_pixel(x, y, r, g, b)