#-*-python-*-
from BaseAI import BaseAI
from GameObject import *

class AI(BaseAI):
  """The class implementing gameplay logic."""
  @staticmethod
  def username():
    return "Shell AI"

  @staticmethod
  def password():
    return "password"

  ##This function is called once, before your first turn
  def init(self):
    self.enemyMinX = 524
    self.enemyMinY = 234
    self.enemyMaxX = 0
    self.enemyMaxY = 0
    self.minX = 300
    self.minY = 300
    self.maxX = 0
    self.maxY = 0
    self.change = -((self.playerID * 2) - 1)
    for droid in self.droids:
      if droid.owner == self.playerID:
        if self.maxX < droid.x:
          self.maxX = droid.x
        if self.maxY < droid.y:
          self.maxY = droid.y
        if self.minX > droid.x:
          self.minX = droid.x
        if self.minY > droid.y:
          self.minY = droid.y
      else:
        if self.enemyMaxX < droid.x:
          self.enemyMaxX = droid.x
        if self.enemyMaxY < droid.y:
          self.enemyMaxY = droid.y
        if self.enemyMinX > droid.x:
          self.enemyMinX = droid.x
        if self.enemyMinY > droid.y:
          self.enemyMinY = droid.y
    self.minY -= 1
    self.maxY += 1
    if self.playerID == 0:
      self.dropX = self.maxX + 1
      self.dropY = self.minY
      self.startX = self.maxX
    else:
      self.dropX = self.minX - 1
      self.dropY = self.minY
      self.startX = self.minX

    pass

  ##This function is called once, after your last turn
  def end(self):
    pass

  ##This function is called each time it is your turn
  ##Return true to end your turn, return false to ask the server for updated information
  def run(self):
    y = self.minY
    notDone = True
    while notDone:
      x = self.minX
      while x <= self.maxX:
        drop = True
        for droid in self.droids:
          if droid.x == x and droid.y == y and droid.owner == self.playerID:
            drop = False
            break
        if drop:
          self.players[self.playerID].orbitalDrop(x, y, 5)
        x += 1
      if y == self.maxY:
        notDone = False
      y = self.maxY

    if self.dropY == self.maxY or self.dropY == self.minY:
      self.players[self.playerID].orbitalDrop((self.mapWidth - 1)*self.playerID, self.dropY, 0)
    else:
      self.players[self.playerID].orbitalDrop(self.dropX, self.dropY, 0)
    self.dropY += 1
    if self.dropY > self.maxY:
      self.dropY = self.minY
    for droid in self.droids:
      if droid.owner == self.playerID and droid.variant != 7 and droid.variant != 5:
        movez = 4
        while movez > 0:
          droid.operate(droid.x + self.change, droid.y)
          #attack around too
          droid.operate(droid.x, droid.y - 1)
          droid.operate(droid.x, droid.y + 1)

          move = True
          for droid2 in self.droids:
            if abs(droid2.y - droid.y) == 1 and droid2.x == droid.x:
              if droid2.variant == 7 and droid2.owner != droid.owner:
                move = False

          if move:
            if droid.x > self.enemyMaxX:
              droid.move(droid.x - 1, droid.y)
            elif droid.x < self.enemyMinX:
              droid.move(droid.x + 1, droid.y)
            
            if not droid.move(droid.x + self.change, droid.y):
              if droid.y == self.maxY:
                droid.move(droid.x, droid.y + 1)
              elif droid.y == self.minY:
                droid.move(droid.x, droid.y - 1)
            if droid.y < self.minY:
              droid.move(droid.x, droid.y + 1)
            elif droid.y > self.maxY:
              droid.move(droid.x, droid.y - 1)

          droid.operate(droid.x + self.change, droid.y)
          #attack around too
          droid.operate(droid.x, droid.y - 1)
          droid.operate(droid.x, droid.y + 1)
          movez -= 1
    return 1

  def __init__(self, conn):
    BaseAI.__init__(self, conn)