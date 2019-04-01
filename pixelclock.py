#!/usr/bin/env python3

import time
from rpi_ws281x import *
import argparse

# LED strip configuration:
LED_COUNT      = 60      # Number of LED pixels.
LED_PIN        = 18      # GPIO pin connected to the pixels (18 uses PWM!).
LED_FREQ_HZ    = 800000  # LED signal frequency in hertz (usually 800khz)
LED_DMA        = 10      # DMA channel to use for generating signal (try 10)
LED_BRIGHTNESS = 255     # Set to 0 for darkest and 255 for brightest
LED_INVERT     = False   # True to invert the signal (when using NPN transistor level shift)
LED_CHANNEL    = 0       # set to '1' for GPIOs 13, 19, 41, 45 or 53


Aqua    = Color(0x00, 0xFF, 0xFF)
Black   = Color(0x00, 0x00, 0x00)
Blue    = Color(0x00, 0x00, 0xFF)
Cyan    = Color(0x00, 0xFF, 0xFF)
Gold    = Color(0xFF, 0xD7, 0x00)
Gray    = Color(0x80, 0x80, 0x80)
Green   = Color(0x00, 0x80, 0x00)
Lime    = Color(0x00, 0xFF, 0x00)
Magenta = Color(0xFF, 0x00, 0xFF)
Navy    = Color(0x00, 0x00, 0x80)
Olive   = Color(0x80, 0x80, 0x00)
Purple  = Color(0x80, 0x00, 0x80)
Red     = Color(0xFF, 0x00, 0x00)
Teal    = Color(0x00, 0x80, 0x80)
White   = Color(0xFF, 0xFF, 0xFF)
Yellow  = Color(0xFF, 0xFF, 0x00)


def clear(strip):
    for i in range(strip.numPixels()):
        strip.setPixelColor(i, Black)
    strip.show()

def scale(color, factor):
    return (int(((color&0xff0000)*factor))&0xff0000) | (int(((color&0x00ff00)*factor))&0x00ff00) | (int(((color&0x0000ff)*factor))&0x0000ff)

# A g_offset of -2 moves the zeroeth position to where the
# connector is located
g_offset = -2
def setPixel(strip, pos, color):
    """
    set pixel at logical position pos to color
    pos can be (slightly) negative or greater than
    numPixels.
    physical position is reversed on the ring and we
    also cater for some offset to move position 0 to
    some other point on the ring
    """
    n = strip.numPixels()
    pos = (n - 1) - ((g_offset + pos + n) % n)
    strip.setPixelColor(pos, color)

def getPixel(strip, pos):
    n = strip.numPixels()
    pos = (n - 1) - ((g_offset + pos + n) % n)
    return strip.getPixelColor(pos)

def sumcolor(c1, c2):
    return Color(min((c1>>16) + (c2>>16), 0xff), min(((c1>>8) + (c2>>8))&0xff, 0xff), min((c1 + c2) & 0xff, 0xff))

def sweep(strip):
    color_sec = scale(Red, 0.5)
    color_min = scale(Green, 1.0)
    color_hour = scale(Blue, 1.0)

    color_back = Black
    color_5 = Color(5,5,5)
    color_15 = Color(20, 20, 20)
    debugging = False
    if debugging:
        startFrame = time.time()

    decoration = [color_back for _ in range(strip.numPixels())]
    for ii in range(0, strip.numPixels(), 5):
        decoration[ii] = color_5

    for ii in range(0, strip.numPixels(), 15):
        decoration[ii] = color_15
        
    for ii in range(0, strip.numPixels()):
        setPixel(strip, ii, decoration[ii])

    while True:

        if not debugging:
            startFrame = time.time()
        now = time.localtime(startFrame)

        # the current second
        pos_s = now.tm_sec
        # the next second 
        pos_s1 = (pos_s + 1) % strip.numPixels()

        # compute the relative brightness of the pixels
        # by scaling using the fractional part of this second
        frac = startFrame % 1
        col_s = scale(color_sec, 1.0 - frac)
        col_s1 = scale(color_sec, frac)
        
        # For the minute indicator.
        pos_m = now.tm_min
        pos_m1 = (pos_m + 1) % strip.numPixels()

        # Fades between 2 pixels as the minute progresses, we
        # calculate using number of milliseconds elapsed for a
        # smoother animation.
        s = ((now.tm_sec + frac) * 1000) / 60000.0

        col_m = scale(color_min, 1.0 - s)
        col_m1 = scale(color_min, s)

        # For the hour indicator.
        h = now.tm_hour % 12
        pos_h = int((h * 60 + now.tm_min) / 12)
        pos_h1 = (pos_h + 1) % strip.numPixels()
        
        # Fade relative to the elapsed seconds in a 12 minute period.
        # (The hour indicator moves one position for each 12 minutes)
        s = (now.tm_min * 60 + now.tm_sec) % 720 / 719.0
        col_h = scale(color_hour, 1.0 - s)
        col_h1 = scale(color_hour, s)

        setPixel(strip, pos_s,  sumcolor(col_s, getPixel(strip, pos_s)))
        setPixel(strip, pos_s1,  sumcolor(col_s1, getPixel(strip, pos_s1)))

        setPixel(strip, pos_m, sumcolor(col_m, getPixel(strip, pos_m)))
        setPixel(strip, pos_m1, sumcolor(col_m1, getPixel(strip, pos_m1)))

        setPixel(strip, pos_h, sumcolor(col_h, getPixel(strip, pos_h)))
        setPixel(strip, pos_h1, sumcolor(col_h1, getPixel(strip, pos_h1)))


        strip.show()

        for pos in [pos_s, pos_s1, pos_m, pos_m1, pos_h, pos_h1]:
            setPixel(strip, pos, decoration[pos])

        if debugging:
            startFrame = startFrame + 0.2
        else:
            refresh_ms = 1000 / 25 # aim for 25 frames per second
            delay_ms = refresh_ms - int(round((time.time() - startFrame) * 1000))
            if delay_ms > 0:
                # Seeing delay_ms of around 38ms on pi3, CPU usage of < 5%
                # print delay_ms
                time.sleep(delay_ms / 1000.0)



# Main program logic follows:
if __name__ == '__main__':
    # Process arguments
    parser = argparse.ArgumentParser()
    parser.add_argument('-c', '--clear', action='store_true', help='clear the display on exit')
    args = parser.parse_args()

    # Create NeoPixel object with appropriate configuration.
    strip = Adafruit_NeoPixel(LED_COUNT, LED_PIN, LED_FREQ_HZ, LED_DMA, LED_INVERT, LED_BRIGHTNESS, LED_CHANNEL, WS2811_STRIP_GRB)
    # Intialize the library (must be called once before other functions).
    strip.begin()

    print ('Press Ctrl-C to quit.')
    if not args.clear:
        print('Use "-c" argument to clear LEDs on exit')

    try:
        sweep(strip)

    except KeyboardInterrupt:
        if args.clear:
            clear(strip)



