#!/usr/bin/env python
"""
nailcast.py - Simulate nail shadows

Author: Jeff Breidenbach
        Francois Lefevere
 
"""

from Numeric import arange
import random
import os
import sys
import math
import Image
import ImageChops
import ImageFilter
from euclid import *
from stl import *

canvas_width_mm = 280.0
margin_mm = 10.0
triangle_side_mm = 8.0
thickness_mm = 3.0
light_dist_mm = 4000

class Nail:
    # x, y coordinates of the nail in pixels,
    # direction: 0,1,2 (determines the color)
    # length: length of the nail [0-1]
    def __init__(self, x, y, direction, length):
      self.x = x
      self.y = y
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
#        print i
        for j in range(0, self.nx + 1):
          dj = (i % 2) * 0.5
          self.AddTriangle(stl, j+0.5-dj, i)

          stl.AddFacet(STLFacet(self.Point(j+0.5+dj, i, 0),
                                self.Point(j-0.5+dj, i, 0),
                                self.Point(j+dj, i+1, 0)), 1)

      print self.nailhash.keys()
      print "hits = %d expected %d " % (self.nailhits,len(self.nails))



# Inverse pyramid
#  b      c
#    \   /
#     \ /
#      |
#      |
#      a
def InvPyramid(center, halftone, mesh):
    mesh.AddNail(Nail(center[0], center[1], 0, halftone[0]))
    mesh.AddNail(Nail(center[0], center[1], 1, halftone[1]))
    mesh.AddNail(Nail(center[0], center[1], 2, halftone[2]))
    return 3

# Lay out a whole bunch of regularly spaced pyramids
def artwork2(offset, im, mesh):
    global canvas_width_mm
    global triangle_side_mm
    ctr = 0
    for x in arange(offset[0], canvas_width_mm, triangle_side_mm):
        for y in arange(offset[1], canvas_width_mm, triangle_side_mm):
            ix = int(x)
            iy = int(y)
            halftone = [0, 0, 0]
            ctr += InvPyramid((x, y), halftone, mesh)
    return ctr

def CreatePovFile(povname, povinclude):
  center = Vector3(canvas_width_mm / 2, canvas_width_mm / 2, 0)
  camera = center + Vector3(0, 0, -0.5 * canvas_width_mm)
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

def main():
    global canvas_width_mm
    global triangle_side_mm
    global margin_mm
    mesh = MeshGenerator(triangle_side_mm, margin_mm)
    if len(sys.argv) == 2:
        infile = sys.argv[1]
    else:
        infile = "Lenna.png"
    im = Image.open(infile)
    nailcount = 0
    nailcount += artwork2((0, 0), im, mesh)
    stl = STL("/tmp/test.stl", "/tmp/test.pov", "Header")
    mesh.Render(stl);
    stl.Close()
    CreatePovFile("/tmp/main.pov", "/tmp/test.pov")
    print "%d nails, max nail size %01f mm" % (nailcount, triangle_side_mm)

if __name__ == '__main__': main()
