__author__ = "Juan C. Caicedo, caicedo@illinois.edu"

import time
import utils as cu
import libDetection as det
import numpy as np
import Image
import random

import RLConfig as config

# ACTIONS
X_COORD_UP         = 0
Y_COORD_UP         = 1
SCALE_UP           = 2
ASPECT_RATIO_UP    = 3
X_COORD_DOWN       = 4
Y_COORD_DOWN       = 5
SCALE_DOWN         = 6
ASPECT_RATIO_DOWN  = 7
PLACE_LANDMARK     = 8

# BOX LIMITS
MIN_ASPECT_RATIO = 0.20
MAX_ASPECT_RATIO = 5.00
MIN_BOX_SIDE     = 20
STEP_FACTOR      = 0.10
DELTA_SIZE       = 0.10

# OTHER DEFINITIONS
NUM_ACTIONS = 9

def fingerprint(b):
  return '_'.join( map(str, map(int, b)) )

class BoxSearchState():

  def __init__(self, imageName, randomStart=False):
    self.imageName = imageName
    self.visibleImage = Image.open(config.get('imageDir') + '/' + self.imageName + '.jpg')
    if not randomStart:
      self.box = map(float, [0,0,self.visibleImage.size[0]-1,self.visibleImage.size[1]-1])
      self.boxW = self.box[2]+1.0
      self.boxH = self.box[3]+1.0
      self.aspectRatio = self.boxH/self.boxW
    else:
      a = random.randint(MIN_BOX_SIDE, self.visibleImage.size[0] - MIN_BOX_SIDE)
      b = random.randint(MIN_BOX_SIDE, self.visibleImage.size[1] - MIN_BOX_SIDE)
      c = random.randint(MIN_BOX_SIDE, min(self.visibleImage.size[0] - a, a) )
      d = random.randint(MIN_BOX_SIDE, min(self.visibleImage.size[1] - b, b) )
      self.box = map(float, [a-c, b-d, a+c, b+d] )
      self.boxW = 2.0*c
      self.boxH = 2.0*d
      self.aspectRatio = self.boxH/self.boxW
    self.landmarkIndex = {}
    self.actionChosen = 2
    self.actionValue = 0

  def performAction(self, action):
    self.actionChosen = action[0]
    self.actionValue = action[1]

    if action[0] == X_COORD_UP:           newBox = self.xCoordUp()
    elif action[0] == Y_COORD_UP:         newBox = self.yCoordUp()
    elif action[0] == SCALE_UP:           newBox = self.scaleUp()
    elif action[0] == ASPECT_RATIO_UP:    newBox = self.aspectRatioUp()
    elif action[0] == X_COORD_DOWN:       newBox = self.xCoordDown()
    elif action[0] == Y_COORD_DOWN:       newBox = self.yCoordDown()
    elif action[0] == SCALE_DOWN:         newBox = self.scaleDown()
    elif action[0] == ASPECT_RATIO_DOWN:  newBox = self.aspectRatioDown()
    elif action[0] == PLACE_LANDMARK:     newBox = self.placeLandmark()

    self.box = newBox
    self.boxW = self.box[2] - self.box[0]
    self.boxH = self.box[3] - self.box[1]
    return self.box

  def xCoordUp(self):
    newBox = self.box[:]
    step = STEP_FACTOR*self.boxW
    # This action preserves box width and height
    if self.box[0] + step + self.boxW < self.visibleImage.size[0]:
      newBox[0] += step
      newBox[2] += step
    else:
      newBox[0] = self.visibleImage.size[0] - self.boxW - 1
      newBox[2] = self.visibleImage.size[0] - 1
    return self.adjustAndClip(newBox)

  def yCoordUp(self):
    newBox = self.box[:]
    step = STEP_FACTOR*self.boxH
    # This action preserves box width and height
    if self.box[1] + step + self.boxH < self.visibleImage.size[1]:
      newBox[1] += step
      newBox[3] += step
    else:
      newBox[1] = self.visibleImage.size[1] - self.boxH - 1
      newBox[3] = self.visibleImage.size[1] - 1
    return self.adjustAndClip(newBox)

  def scaleUp(self):
    newBox = self.box[:]
    # This action preserves aspect ratio
    widthChange = DELTA_SIZE*self.boxW
    heightChange = DELTA_SIZE*self.boxH
    if self.boxW + widthChange < self.visibleImage.size[0]:
      if self.boxH + heightChange < self.visibleImage.size[1]:
        newDelta = DELTA_SIZE
      else:
        newDelta = self.visibleImage.size[1]/self.boxH - 1
    else:
      newDelta = self.visibleImage.size[0]/self.boxW - 1
      if self.boxH + newDelta*self.boxH >= self.visibleImage.size[1]:
        newDelta = self.visibleImage.size[1]/self.boxH - 1
    widthChange = newDelta*self.boxW/2.0
    heightChange = newDelta*self.boxH/2.0
    newBox[0] -= widthChange
    newBox[1] -= heightChange
    newBox[2] += widthChange
    newBox[3] += heightChange
    return self.adjustAndClip(newBox)

  def aspectRatioUp(self):
    newBox = self.box[:]
    # This action preserves width
    heightChange = DELTA_SIZE*self.boxH
    if self.boxH + heightChange < self.visibleImage.size[1]:
      ar = (self.boxH + heightChange)/self.boxW
      if ar < MAX_ASPECT_RATIO:
        newDelta = DELTA_SIZE
      else:
        newDelta = 0.0
    else:
      newDelta = self.visibleImage.size[1]/self.boxH - 1
      ar = (self.boxH + newDelta*self.boxH)/self.boxW
      if ar > MAX_ASPECT_RATIO:
        newDelta =  0.0
    heightChange = newDelta*self.boxH/2.0
    newBox[1] -= heightChange
    newBox[3] += heightChange
    return self.adjustAndClip(newBox)

  def xCoordDown(self):
    newBox = self.box[:]
    step = STEP_FACTOR*self.boxW
    # This action preserves box width and height
    if self.box[0] - step >= 0:
      newBox[0] -= step
      newBox[2] -= step
    else:
      newBox[0] = 0
      newBox[2] = self.boxW
    return self.adjustAndClip(newBox)

  def yCoordDown(self):
    newBox = self.box[:]
    step = STEP_FACTOR*self.boxH
    # This action preserves box width and height
    if self.box[1] - step >= 0:
      newBox[1] -= step
      newBox[3] -= step
    else:
      newBox[1] = 0
      newBox[3] = self.boxH
    return self.adjustAndClip(newBox)

  def scaleDown(self):
    newBox = self.box[:]
    # This action preserves aspect ratio
    widthChange = DELTA_SIZE*self.boxW
    heightChange = DELTA_SIZE*self.boxH
    if self.boxW - widthChange >= MIN_BOX_SIDE:
      if self.boxH - heightChange >= MIN_BOX_SIDE:
        newDelta = DELTA_SIZE
      else:
        newDelta = MIN_BOX_SIDE/self.boxH - 1
    else:
      newDelta = MIN_BOX_SIDE/self.boxW - 1
      if self.boxH - newDelta*self.boxH < MIN_BOX_SIDE:
        newDelta = MIN_BOX_SIDE/self.boxH - 1
    widthChange = newDelta*self.boxW/2.0
    heightChange = newDelta*self.boxH/2.0
    newBox[0] += widthChange
    newBox[1] += heightChange
    newBox[2] -= widthChange
    newBox[3] -= heightChange
    return self.adjustAndClip(newBox)

  def aspectRatioDown(self):
    newBox = self.box[:]
    # This action preserves height
    widthChange = DELTA_SIZE*self.boxW
    if self.boxW + widthChange < self.visibleImage.size[0]:
      ar = self.boxH/(self.boxW + widthChange)
      if ar >= MIN_ASPECT_RATIO:
        newDelta = DELTA_SIZE
      else:
        newDelta = 0.0
    else:
      newDelta = self.visibleImage.size[0]/self.boxW - 1
      ar = self.boxH/(self.boxW + newDelta*self.boxW)
      if ar < MIN_ASPECT_RATIO:
        newDelta =  0.0
    widthChange = newDelta*self.boxW/2.0
    newBox[0] -= widthChange
    newBox[2] += widthChange
    return self.adjustAndClip(newBox)

  def adjustAndClip(self, box):
    if box[0] < 0:
      # Can we move it to the right?
      step = -box[0]
      if box[2] + step < self.visibleImage.size[0]:
        box[0] += step
        box[2] += step
      else:
        box[0] = 0
        box[2] = self.visibleImage.size[0] - 1
    if box[1] < 0:
      step = -box[1]
      # Can we move it down?
      if box[3] + step < self.visibleImage.size[1]:
        box[1] += step
        box[3] += step
      else:
        box[1] = 0
        box[3] = self.visibleImage.size[1] - 1
    if box[2] >= self.visibleImage.size[0]:
      step = box[2] - self.visibleImage.size[0]
      # Can we move it to the left?
      if box[0] - step >= 0:
        box[0] -= step
        box[2] -= step
      else:
        box[0] = 0
        box[2] = self.visibleImage.size[0] - 1
    if box[3] >= self.visibleImage.size[1]:
      step = box[3] - self.visibleImage.size[1]
      # Can we move it up?
      if box[1] - step >= 0:
        box[1] -= step
        box[3] -= step
      else:
        box[1] = 0
        box[3] = self.visibleImage.size[1] - 1
    return box

  def placeLandmark(self):
    self.landmarkIndex[ fingerprint(self.box) ] = self.box[:]
    newBox = map(float, [0,0,self.visibleImage.size[0]-1,self.visibleImage.size[1]-1])
    return newBox

  def getRepresentation(self):
    # Proximity features (8)
    ious = []
    for fp in self.landmarkIndex.keys():
      ious.append( det.IoU( self.box, self.landmarkIndex[fp] ) )
    ious.sort(reverse=True)
    ious = ious[0:8]
    while len(ious) < 8:
      ious.append(0.0)
    return ious

  def visitedBefore(self):
    fp = fingerprint(self.box)
    try: v = len(self.landmarkIndex[fp])
    except: v = 0
    if v > 0:
      return True
    else:
      return False
