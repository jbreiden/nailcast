#!/usr/bin/env python
"""\
nailcast.py - Simulate nail shadows

Makes use (and directly copies some code from) the example
program SVG.py found on ActiveState.

http://aspn.activestate.com/ASPN/Cookbook/Python/Recipe/325823

Input: image
Output: nail shadow halftone simulation

"""

import random
import os
import math
import Image
import ImageChops
display_prog = 'display' # Command to execute to display images.

class Scene:
    def __init__(self,name="svg",height=400,width=400):
        self.name = name
        self.items = []
        self.height = height
        self.width = width
        return

    def add(self,item): self.items.append(item)

    def strarray(self):
        var = ["<?xml version=\"1.0\"?>\n",
               "<svg height=\"%d\" width=\"%d\" >\n" % (self.height,self.width),
               " <g style=\"fill-opacity:1.0; stroke:black;",
               " stroke-width:1; \">\n"]
        for item in self.items: var += item.strarray()
        var += [" </g>\n</svg>\n"]
        return var

    def write_svg(self,filename=None):
        if filename:
            self.svgname = filename
        else:
            self.svgname = self.name + ".svg"
        file = open(self.svgname,'w')
        file.writelines(self.strarray())
        file.close()
        return

    def display(self,prog=display_prog):
        os.system("%s %s" % (prog,self.svgname))
        return

class Line:
    def __init__(self,start,end, color, width):
        self.start = start  #xy tuple
        self.end = end      #xy tuple
        self.color = color  #rgb tuple in range(0,256)
        self.width = width
        return

    def strarray(self):
        return ["  <line x1=\"%d\" y1=\"%d\" x2=\"%d\" y2=\"%d\" " %\
                (self.start[0],self.start[1],self.end[0],self.end[1]),
                "style=\"stroke:%s; stroke-width:2;\" />\n" % colorstr(self.color) ]

class Circle:
    def __init__(self,center,radius,color):
        self.center = center #xy tuple
        self.radius = radius #xy tuple
        self.color = color   #rgb tuple in range(0,256)
        return

    def strarray(self):
        return ["  <circle cx=\"%d\" cy=\"%d\" r=\"%d\" " %\
                (self.center[0],self.center[1],self.radius),
                "style=\"fill:%s; stroke-width:1;\"  />\n" % colorstr(self.color)]

def colorstr(rgb): return "#%x%x%x" % (rgb[0]/16,rgb[1]/16,rgb[2]/16)

def some(a,b,fraction):
    return (a[0] + fraction * (b[0] - a[0]),
            a[1] + fraction * (b[1] - a[1]))

def Pyramid(scene, center, s, r, halftone):
    w = 2
    yellow = (255, 255, 0)
    cyan = (0, 255, 255)
    magenta = (255, 0, 255)
    blue = (0, 0, 255)
    green = (0, 255, 0)
    red = (255, 0, 0)
    a = (center[0], center[1] - r) # top
    b = (center[0] + s/2, center[1] + r) # bottom right
    c = (center[0] - s/2, center[1] + r) # bottom left
    ab_tip = some(a,b,halftone[0])
    ac_tip = some(a,c,halftone[0])
    ba_tip = some(b,a,halftone[1])
    bc_tip = some(b,c,halftone[1])
    ca_tip = some(c,a,halftone[2])
    cb_tip = some(c,b,halftone[2])
    scene.add(Line(a, ab_tip, magenta, w))
    scene.add(Line(a, ac_tip, yellow, w))
    scene.add(Line(b, ba_tip, cyan, w))
    scene.add(Line(b, bc_tip, yellow, w))
    scene.add(Line(c, ca_tip, cyan, w))
    scene.add(Line(c, cb_tip, magenta, w))
    if ab_tip[0] > ba_tip[0]:
        scene.add(Line(ab_tip, ba_tip, blue, w))
    if bc_tip[0] < cb_tip[0]:
        scene.add(Line(bc_tip, cb_tip, red, w))
    if ca_tip[0] > ac_tip[0]:
        scene.add(Line(ac_tip, ca_tip, green, w))
    scene.add(Circle(a, w/2, (255,255,255)))
    scene.add(Circle(c, w/2, (255,255,255)))
    scene.add(Circle(b, w/2, (255,255,255)))

def rgb2abc(rgb):
    return ((+ rgb[0] - rgb[1] - rgb[2] + 255) / 255.0,
            (- rgb[0] + rgb[1] - rgb[2] + 255) / 255.0,
            (- rgb[0] - rgb[1] + rgb[2] + 255) / 255.0)

def get_cell_color_analytic(x,y,im):
    rgb = im.getpixel((x,y))
    alpha = 1
    y = round(0.299 * rgb[0] + 0.144 * rgb[1] + 0.615 * rgb[2])
    a = -1
    b = -1
    c = -1
    lookup = rgb2abc(rgb)
    while a < 0 or b < 0 or c < 0 or a > 1 or b > 1 or c > 1:
        if (alpha < -0.2):
            print "bug"
            break
        a, b, c = rgb2abc((alpha * rgb[0]  + (1 - alpha) * y,
                           alpha * rgb[1]  + (1 - alpha) * y,
                           alpha * rgb[2]  + (1 - alpha) * y))
        alpha = alpha - 0.1
    return (a, b, c)

def artwork(scene, offset, s, r, im):
    for y in range(int(offset[1]), im.size[1], int(r*4)):
        if y >= 0:
            for x in range(offset[0], im.size[0], s):
                Pyramid(scene,(x, y),
                        s, r, get_cell_color_analytic(x,y,im))
            for x in range(offset[0] + s/2, im.size[0], s):
                Pyramid(scene,(x, y + 2 * r),
                        s, r, get_cell_color_analytic(x,y,im))
    return

def portrait():
    s = 10   # Max length of a nail
    im = Image.open("Lenna.png")
    scale = 1024 / im.size[1];
    im = im.resize((scale * im.size[0], scale * im.size[1]))
    r = math.sqrt(s * s - s * s / 4) / 2
    scene = Scene('test', im.size[0], im.size[1])
    makeitwork = math.tan(math.pi/6) * 0.5 * s
    artwork(scene, (0,0), s, r, im)
    artwork(scene, (s/2, - makeitwork), s, r, im)
    scene.write_svg()
    scene.display()

if __name__ == '__main__': portrait()
