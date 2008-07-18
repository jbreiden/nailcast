#!/usr/bin/python
import struct
from euclid import *
from math import *

def PrintVector(v):
  return "<%.1f,%.1f,%.1f>" % (v[0], v[1], v[2])

class STLFacet:
  def __init__(self, v1, v2, v3, att_bc=0):
    normal = (v2 - v1).cross(v3 - v1)
    if normal.magnitude_squared() > 1E-4:
      normal = normal.normalized()
      self.valid = 1
    else:
      self.valid = 0
    self.coords = [normal, v1, v2, v3]
    self.att_bc = att_bc

  def Print(self, pov):
    return "triangle{%s,%s,%s}" % (PrintVector(self.coords[1]),
                                     PrintVector(self.coords[2]),
                                     PrintVector(self.coords[3]))

class STL:
  def __init__(self, fname, povname, header):
    self.f = open(fname, "w")
    self.pov = open(povname, "w")
    self.facedata = []
    self.nfaces = 0

    # Write Header
    out = ['%-80.80s' % header]
    # Temporarily set # of faces to 0
    out.append(struct.pack('L',0))
    self.f.write(''.join(out))
    self.povgroups = [[], []]

  def Close(self):
    self.Flush()
    self.f.seek(80);
    out = []
    out.append(struct.pack('L', self.nfaces))
    self.f.write(''.join(out))
    self.f.close()
    print >>self.pov, "mesh{"
    for s in self.povgroups[0]:
      print >>self.pov, s
    print >>self.pov, "pigment{color rgb<0,0,0>}"
    print >>self.pov, "}"
    print >>self.pov, "mesh{"
    for s in self.povgroups[1]:
      print >>self.pov, s
    print >>self.pov, "pigment{color rgb<1,1,1>}"
    print >>self.pov, "}"
    self.pov.close()

  def AddFacet(self, facet, group):
    if not facet.valid:
      return
    self.nfaces = self.nfaces + 1
    for coord in facet.coords:
      self.facedata.append(struct.pack('3f', *coord))
    #print(facet.coords)
    self.facedata.append(struct.pack('H', facet.att_bc))
    self.povgroups[group].append(facet.Print(self.pov))
    if len(self.facedata) > 65536:
      self.Flush()

  def Flush(self):
    self.f.write(''.join(self.facedata))
    self.facedata = []

  # Draws a cylinder connected to a triangle equilateral of side = trsize
  def AddCylinder(self, bottom, top, radius, prec, trsize):
    trradius = trsize / sqrt(3)
    trpoints = []
    for i in range(0,3):
      trpoints.append(bottom + trsize * Vector3(cos((2*i+1)*pi/3), sin((2*i+1)*pi/3), 0))

    prec3 = int(prec / 3)
    p = []
    for i in range(0, prec):
      dangle = 2 * math.pi / prec
      a0 = i * dangle
      a1 = a0 + dangle
      r0 = radius * Vector3(cos(a0), sin(a0), 0)
      r1 = radius * Vector3(cos(a1), sin(a1), 0)
      # self.AddFacet(STLFacet(bottom, bottom + r1, bottom + r0))
      self.AddFacet(STLFacet(bottom + r0, bottom + r1, top + r1))
      self.AddFacet(STLFacet(top + r1, top + r0, bottom + r0))
      self.AddFacet(STLFacet(top, top + r0, top + r1))

      #self.AddFacet(STLFacet(bottom + r0, trpoints[int(i / prec3)], bottom + r1))
      if i % prec3 == 0:
        p = p + [ r0 ]
    #self.AddFacet(STLFacet(trpoints[0], trpoints[1], p[1]))
    #self.AddFacet(STLFacet(trpoints[1], trpoints[2], p[2]))
    #self.AddFacet(STLFacet(trpoints[2], trpoints[0], p[0]))
    self.AddFacet(STLFacet(trpoints[0], trpoints[1], trpoints[2]))



def test():
   stl=STL('/tmp/test.stl', 'Header ...')
   stl.AddCylinder(Vector3(0, 0, 0), Vector3(5, 2, 8), 4, 21, 300)
   stl.Close();

#test()
