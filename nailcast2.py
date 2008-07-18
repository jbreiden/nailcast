#!/usr/bin/env python
"""
nailcast.py - Simulate nail shadows

Author: Jeff Breidenbach

This program contains code snippets from
http://aspn.activestate.com/ASPN/Cookbook/Python/Recipe/325823

"""

import random
import os
import sys
import math
import Image
import ImageChops
import ImageFilter
from euclid import *
from stl import *
display_prog = 'rsvg' # Command to execute to display images.

screen_ppi = 92.0
screen_pixels_per_mm = screen_ppi / 25.4
canvas_width_mm = 280.0
margin_mm = 10.0
canvas_pixels = canvas_width_mm * screen_pixels_per_mm
triangle_side_mm = 8.0
# thickness of the board
thickness_mm = 3.0
# Distance of the light sources
light_dist_mm = 4000

class Nail:
    # x, y coordinates of the nail in pixels,
    # direction: 0,1,2 (determines the color)
    # length: length of the nail [0-1]
    def __init__(self, x, y, direction, length):
      self.x = x / screen_pixels_per_mm
      self.y = y / screen_pixels_per_mm
      self.direction = direction
      self.length = length

# Convert from integer direction 0,1,2 to actual 3d coordinates.
# The return vector is normalized
def LightDirection(direction):
  alpha = direction * 2 * pi / 3
  cosbeta = sqrt(1.0/3.0)
  sinbeta = sqrt(2.0/3.0)
  return Vector3(-sin(alpha)*cosbeta, cos(alpha)*cosbeta, -sinbeta)

class MeshGenerator:
    def __init__(self, triangle_side_mm, margin_mm):
      self.nails = []
      self.triangle_side_mm = triangle_side_mm
      self.dx = self.triangle_side_mm / 6.0
      self.dy = self.dx * sqrt(3) / 2.0
      self.margin_mm = margin_mm;

    def AddNail(self, nail):
      self.nails.append(nail)

    def GetExtent(self):
      minx = 1000000
      miny = 1000000
      maxx = -minx
      maxy = -miny
      for nail in self.nails:
        minx = min(minx, nail.x)
        miny = min(miny, nail.y)
        maxx = max(maxx, nail.x)
        maxy = max(maxy, nail.y)
      self.nx = int((2 * self.margin_mm + maxx - minx) / self.dx)
      self.ny = int((2 * self.margin_mm + maxy - miny) / self.dy)
      # Make sure the nails are aligned with the triangle grid
      self.x0 = minx - (0.5 + int(self.margin_mm / self.dx)) * self.dx
      self.y0 = miny - int(self.margin_mm / self.dy / 2) * self.dy * 2

    def CreateNailHash(self):
      self.nailhash = {}
      self.nailhits = 0
      for nail in self.nails:
        x = (nail.x - self.x0) / self.dx
        y = (nail.y - self.y0) / self.dy
        if nail.direction == 1:
          x = x - 0.5
          y = y - 1
        if nail.direction == 2:
          x = x + 0.5
          y = y - 1
        key = (int(round(x * 2)), int(round(y * 2)))
        self.nailhash[key] = nail

    def FindNail(self, x, y):
      key = (int(round(x * 2)), int(round(y * 2)))
      if self.nailhash.has_key(key):
        self.nailhits = self.nailhits + 1
        return self.nailhash[key]
      return None

    def Point(self, x, y, z):
      x = min(self.nx, max(x, 0))
      y = min(self.ny, max(y, 0))
      return Vector3(x*self.dx, y*self.dy, z)

    def AddTriangle(self, stl, x, y):
      base = [self.Point(x, y, 0),
              self.Point(x - 0.5, y + 1, 0),
              self.Point(x + 0.5, y + 1, 0)]
      nail = self.FindNail(x, y)
      if nail:
        top = []
        for i in range(0, 3):
          length = triangle_side_mm * 5.0 / 6.0 * nail.length
          #alpha = nail.direction * 2 * pi / 3
          #cosbeta = sqrt(1.0/3.0)
          #sinbeta = sqrt(2.0/3.0)
          #top.append(base[i] + length * Vector3(-sin(alpha)*cosbeta, cos(alpha)*cosbeta, -sinbeta))
          top.append(base[i] + length * LightDirection(nail.direction))
        stl.AddFacet(STLFacet(top[0], top[1], top[2]),0)
        for i in range(0, 3):
          i1 = (i + 1) % 3
          stl.AddFacet(STLFacet(base[i], base[i1], top[i1]),0)
          stl.AddFacet(STLFacet(base[i], top[i1], top[i]),0)
      else:
        stl.AddFacet(STLFacet(base[0], base[1], base[2]),1)

    def AddQuad(self, stl, p0, p1, p2, p3):
      stl.AddFacet(STLFacet(p0, p2, p1), 1)
      stl.AddFacet(STLFacet(p0, p3, p2), 1)

    def Render(self, stl):
      self.GetExtent()
      self.CreateNailHash()
      # Generate the base :
      print "nx=%d ny=%d" % (self.nx, self.ny)

      corners = []
      for i in range(0, 8):
        i0 = i % 2
        j0 = int(i/2) % 2
        k0 = int(i/4) % 2
        corners.append(self.Point(i0 * self.nx,
                                  j0 * self.ny,
                                  k0 * thickness_mm))
      self.AddQuad(stl, corners[4], corners[6], corners[7], corners[5])
      self.AddQuad(stl, corners[2], corners[3], corners[7], corners[6])
      self.AddQuad(stl, corners[3], corners[1], corners[5], corners[7])
      self.AddQuad(stl, corners[1], corners[0], corners[4], corners[5])
      self.AddQuad(stl, corners[0], corners[2], corners[6], corners[4])

      for i in range(0, self.ny):
        print i
        for j in range(0, self.nx + 1):
          dj = (i % 2) * 0.5
          self.AddTriangle(stl, j+0.5-dj, i)

          stl.AddFacet(STLFacet(self.Point(j+0.5+dj, i, 0),
                                self.Point(j-0.5+dj, i, 0),
                                self.Point(j+dj, i+1, 0)), 1)

      print self.nailhash.keys()
      print "hits = %d expected %d " % (self.nailhits,len(self.nails))





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
               " <g style=\"fill-opacity:1.0; stroke:gray;",
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
        os.system("%s -d 92 %s %s-out.jpg" % (prog, self.svgname, self.name))
        os.system("display %s-out.jpg" % self.name)
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

class Rectangle:
    def __init__(self,origin,height,width,color):
        self.origin = origin
        self.height = height
        self.width = width
        self.color = color
        return

    def strarray(self):
        return ["  <rect x=\"%d\" y=\"%d\" height=\"%d\"\n" %\
                (self.origin[0],self.origin[1],self.height),
                "    width=\"%d\" style=\"fill:%s;\" />\n" %\
                (self.width,colorstr(self.color))]


def colorstr(rgb): return "#%x%x%x" % (rgb[0]/16,rgb[1]/16,rgb[2]/16)

def some(a,b,fraction):
    return (a[0] + fraction * (b[0] - a[0]),
            a[1] + fraction * (b[1] - a[1]))


# Draw the shadows of a pyramid
#
# @scene  - this is just the SVG canvas we draw on
# @center - x,y coordinates of center in final image pixels
# @s - length of a triangle side in final image pixels
# @r - half of the height of an equilatoral triangle in pixels.
#      this could be computed from s, but I got a little bit lazy
#      and didn't want to recompute all over the place (also
#      the calculation requires a square root
# @halftone - (a, b, c) This is the heights of the three nails,
#             and their range is from 0 to 1
#
#
# Bird's eye view:
#
#   green       a     blue     -
#              / \             |
#           s / + \            | 2r
#            /     \           |
#           c-------b          -
#
#              red
def Pyramid(scene, center, s, r, halftone, mesh):
    epsilon = 0.1  # Don't bother for tiny nails
    count = 0 # how many nails did we use?
    w = 2
    yellow = (255, 255, 0)
    cyan = (0, 255, 255)
    magenta = (255, 0, 255)
    blue = (0, 0, 255)
    green = (0, 255, 0)
    red = (255, 0, 0)
    white = (255, 255, 255)
    a = (center[0], center[1] - r) # north
    b = (center[0] + s/2, center[1] + r) # southeast
    c = (center[0] - s/2, center[1] + r) # southwest
    ab_tip = some(a,b,halftone[0])
    ac_tip = some(a,c,halftone[0])
    ba_tip = some(b,a,halftone[1])
    bc_tip = some(b,c,halftone[1])
    ca_tip = some(c,a,halftone[2])
    cb_tip = some(c,b,halftone[2])

    mesh.AddNail(Nail(a[0], a[1], 0, halftone[0]))
    mesh.AddNail(Nail(b[0], b[1], 1, halftone[1]))
    mesh.AddNail(Nail(c[0], c[1], 2, halftone[2]))

    if halftone[0] > epsilon:
        scene.add(Line(a, ab_tip, magenta, w))
        scene.add(Line(a, ac_tip, yellow, w))
        scene.add(Circle(a, w/2, white))
        count += 1
    if halftone[1] > epsilon:
        scene.add(Line(b, ba_tip, cyan, w))
        scene.add(Line(b, bc_tip, yellow, w))
        scene.add(Circle(b, w/2, white))
        count += 1
    if halftone[2] > epsilon:
        scene.add(Line(c, ca_tip, cyan, w))
        scene.add(Line(c, cb_tip, magenta, w))
        scene.add(Circle(c, w/2, white))
        count += 1
    if ab_tip[0] > ba_tip[0]:
        scene.add(Line(ab_tip, ba_tip, blue, w))
    if bc_tip[0] < cb_tip[0]:
        scene.add(Line(bc_tip, cb_tip, red, w))
    if ca_tip[0] > ac_tip[0]:
        scene.add(Line(ac_tip, ca_tip, green, w))
    return count

# Inverse pyramid
#  b      c
#    \   /
#     \ /
#      |
#      |
#      a
def InvPyramid(scene, center, s, r, halftone, mesh):
    mesh.AddNail(Nail(center[0], center[1], 0, halftone[0]))
    mesh.AddNail(Nail(center[0], center[1], 1, halftone[1]))
    mesh.AddNail(Nail(center[0], center[1], 2, halftone[2]))
    return 3

def rgb2abc(rgb):
    return ((+ rgb[0] - rgb[1] - rgb[2] + 255) / 255.0,
            (- rgb[0] + rgb[1] - rgb[2] + 255) / 255.0,
            (- rgb[0] - rgb[1] + rgb[2] + 255) / 255.0)

def get_cell_color_analytic(x,y,im):
    rgb = im.getpixel((x,y))
    alpha = 1
    y = round(0.299 * rgb[0] + 0.587 * rgb[1] + 0.114 * rgb[2])
    a = -1
    b = -1
    c = -1
    lookup = rgb2abc(rgb)
    while a < 0 or b < 0 or c < 0 or a > 1 or b > 1 or c > 1:
        if (alpha < -0.2):
            print "bug - why can't we find RGB %s %s %s" % rgb
            break
        a, b, c = rgb2abc((alpha * rgb[0]  + (1 - alpha) * y,
                           alpha * rgb[1]  + (1 - alpha) * y,
                           alpha * rgb[2]  + (1 - alpha) * y))
        alpha = alpha - 0.1
    return (a, b, c)

# Old complicated method
def artwork(scene, offset, s, r, im, mesh):
    ctr = 0
    for y in range(int(offset[1]), im.size[1], int(r*4)):
        if y >= 0:
            for x in range(offset[0], im.size[0], s):
                ctr += Pyramid(scene,(x, y),
                               s, r, get_cell_color_analytic(x, y, im), mesh)
            for x in range(offset[0] + s/2, im.size[0], s):
                ctr += Pyramid(scene,(x, y + 2 * r),
                               s, r, get_cell_color_analytic(x, y, im), mesh)
    return ctr

# New simpler method
def artwork2(scene, offset, s, r, im, mesh):
    r2 = 4 * r / 3
    ny = int(im.size[1] / r2)
    nx = int(im.size[0] / s)
    ctr = 0

    for i in range(0, ny):
      for j in range(0, nx):
        x = (j + offset[0]) * s
        y = (i + offset[1]) * r2
        ix = int(x)
        iy = int(y)
        if ix < 0 or iy < 0 or ix >= im.size[0] or iy >= im.size[1]:
          continue
        rgb = im.getpixel((x,y))
        halftone = [1,0,0]#[rgb[0]/255.0, rgb[1]/255.0, rgb[2]/255.0]
        ctr += InvPyramid(scene, (x, y), s, r, halftone, mesh)

    return ctr

def CreatePovFile(povname, povinclude):
  center = Vector3(canvas_width_mm / 2, canvas_width_mm / 2, 0)
  camera = center + Vector3(0, 0, -2 * canvas_width_mm)
  pov = open(povname, "w")
  print >>pov, """
camera {
  location %s
  look_at %s
}

// Red
light_source {
  %s
  color rgb <1,0,0>
}

// Green
light_source {
  %s
  color rgb <0,1,0>
}

// Blue
light_source {
  %s
  color rgb <0,0,1>
}
// Geometry
#include "%s"
""" % (PrintVector(camera),
       PrintVector(center),
       PrintVector(center + light_dist_mm * LightDirection(0)),
       PrintVector(center + light_dist_mm * LightDirection(1)),
       PrintVector(center + light_dist_mm * LightDirection(2)),
       povinclude)

def portrait(argv=None):
    if argv is None:
        argv = sys.argv
    global screen_pixels_per_mm
    global screen_ppi
    global screen_pixels_per_mm
    global canvas_width_mm
    global margin_mm
    global canvas_pixels
    global triangle_side_mm

    s = triangle_side_mm * screen_pixels_per_mm  # length of triangle side
    r = math.sqrt(s * s - s * s / 4) / 2
    #s = int(round(s))
    #r = int(round(r))

    mesh = MeshGenerator(triangle_side_mm, margin_mm)

    if len(argv) == 2:
        infile = argv[1]
    else:
        infile = "rooster.jpg"
        #infile = "Lenna.png"
    stem = os.path.splitext(os.path.basename(infile))[0]
    im = Image.open(infile)
    scale = canvas_pixels / im.size[1];
    im = im.resize((int(scale * im.size[0]), int(scale * im.size[1])))
    scene = Scene(stem, im.size[1], im.size[0])
    makeitwork = math.tan(math.pi / 6) * 0.5 * s
    scene.add(Rectangle((0,0),im.size[1], im.size[0], (255,255,255)))
    #count = artwork(scene, (0, r), s, r, im, mesh)
    #count += artwork(scene, (s / 2, r - makeitwork), s, r, im, mesh)

    count = artwork2(scene, (0, 0), s, r, im, mesh)
    count += artwork2(scene, (0.5, 0.5), s, r, im, mesh)

    scene.write_svg()
    print "%d nails, cell size %0.1f mm (%0.1f pixels)" % (count,
                                                           triangle_side_mm,
                                                           s)
    stl = STL("/tmp/test.stl", "/tmp/test.pov", "Header")
    mesh.Render(stl);
    stl.Close()
    CreatePovFile("/tmp/main.pov", "/tmp/test.pov")
    #scene.display()

if __name__ == '__main__': portrait()
