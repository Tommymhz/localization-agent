__author__ = "Juan C. Caicedo, caicedo@illinois.edu"

class SingleObjectLocalizer():

  adjustingPercent = 0.1
  
  # Actions
  ACCEPT         = 0
  REJECT         = 1
  EXPAND_TOP     = 2
  EXPAND_BOTTOM  = 3
  EXPAND_LEFT    = 4
  EXPAND_RIGHT   = 5
  REDUCE_TOP     = 6
  REDUCE_BOTTOM  = 7
  REDUCE_LEFT    = 8
  REDUCE_RIGHT   = 9
  
  def __init__(self, imgSize, initialBox):
    self.prevBox = initialBox
    self.nextBox = initialBox
    self.imgWidth = imgSize[0]
    self.imgHeight = imgSize[1]
    self.lastAction = float("inf")
    self.history = []
    self.terminalScore = 0.0

  def performAction(self, action, values):
    ## Terminal States
    if self.lastAction == self.ACCEPT:
      self.terminalScore = values[self.lastAction]
      return self.lastAction
    if self.lastAction == self.REJECT:
      self.terminalScore = -values[self.lastAction]
      return self.lastAction
    ## Adjust the current box
    elif action == self.EXPAND_TOP:    self.adjustCurrentBox(-1, 'y', 1)
    elif action == self.EXPAND_BOTTOM: self.adjustCurrentBox( 1, 'y', 3)
    elif action == self.EXPAND_LEFT:   self.adjustCurrentBox(-1, 'x', 0)
    elif action == self.EXPAND_RIGHT:  self.adjustCurrentBox( 1, 'x', 2)
    elif action == self.REDUCE_TOP:    self.adjustCurrentBox( 1, 'y', 1)
    elif action == self.REDUCE_BOTTOM: self.adjustCurrentBox(-1, 'y', 3)
    elif action == self.REDUCE_LEFT:   self.adjustCurrentBox( 1, 'x', 0)
    elif action == self.REDUCE_RIGHT:  self.adjustCurrentBox(-1, 'x', 2)
    elif action == self.ACCEPT or action == self.REJECT:
      pass
    else:
      print 'Unknown action',action
      return
    self.lastAction = action
    self.terminalScore = values[0] - values[1] # Q0 - Q1
    self.history.append(action)
    return self.lastAction
      
  def adjustCurrentBox(self, direction, axis, coordinate):
    ''' direction  : -1 or 1
        axis       : x or y
        coordinate : 0,1,2,3
    '''
    if axis == 'x':
      delta = (self.nextBox[2] - self.nextBox[0]) * self.adjustingPercent
      limit = self.imgWidth
    else:
      delta = (self.nextBox[3] - self.nextBox[1]) * self.adjustingPercent
      limit = self.imgHeight

    self.prevBox = [x for x in self.nextBox]
    self.nextBox[coordinate] += direction*delta

    if self.nextBox[coordinate] < 0: 
      self.nextBox[coordinate] = 0
    if self.nextBox[coordinate] >= limit:
      self.nextBox[coordinate] = limit - 1
