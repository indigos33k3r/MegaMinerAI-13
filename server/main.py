#!/usr/bin/env python2
# -*- coding: iso-8859-1 -*-
from networking.sexpr.sexpr import sexpr2str
from networking.dispatch import SexpProtocol
from networking.apps import BaseApp, protocolmethod, namedmethod, AccountsAppMixin
from itertools import repeat
import functools
import game_app.match
Match = game_app.match.Match
from game_app.game_app_utils import errorBuffer, requireLogin, requireGame,                   requireTurn, requireTypes
import time
import struct
import bz2
import sys

class GameApp(AccountsAppMixin, BaseApp):
  games = {}
  nextid = 1
  def __init__(self, protocol):
    BaseApp.__init__(self, protocol)
    AccountsAppMixin.__init__(self)
    self.game = None
    self.user = self.name
    self.screenName = self.name

  @protocolmethod
  @requireLogin
  def createGame(self):
    """ Creates a game """
    if self.game is not None:
      return ("create-game-denied", "You are already in a game.")
    else:
      while GameApp.nextid in GameApp.games:
        GameApp.nextid += 1
      print "Creating game %d"%(GameApp.nextid,)
      self.user = self.name
      self.screenName = self.name
      self.game = Match(GameApp.nextid, self)
      self.game.addPlayer(self)
      GameApp.games[GameApp.nextid] = self.game
      GameApp.nextid += 1
      return ("create-game", self.game.id)

  @protocolmethod
  @requireLogin
  @requireTypes(None, int, str)
  def joinGame(self, gameNumber, playerType):
    """ Joins the specified game"""    
    if self.game is not None:
      return ["join-game-denied", "You are already in a game"]
    try:
      self.user = self.name
      self.screenName = self.name
      if gameNumber == 0: #join any option, joins available game with lowest number
        for game in GameApp.games:
          self.game = GameApp.games[game]
          temp = self.game.addPlayer(self, playerType)
          if temp and type(temp) == type(bool()):
            gameNumber = game
            break
          else:
            self.game = None
        if self.game is None:
          return ["join-game-denied", "No games available"]
      else: #join a specific game, gameNumber >= 1
        self.game = GameApp.games[gameNumber]
        temp = self.game.addPlayer(self, playerType)
        if type(temp) != type(bool()) or not temp:
          self.game = None
          return ["join-game-denied", "Game is full"]
      return ["join-accepted", gameNumber]
    except KeyError:
      self.game = Match(gameNumber, self)
      self.game.addPlayer(self)
      GameApp.games[gameNumber] = self.game
      return ["create-game", self.game.id]

  @protocolmethod
  @errorBuffer
  @requireGame
  def leaveGame(self):
    """ Leaves the current game """
    if self.game is None:
      return "Not in a game"
    reply = self.game.removePlayer(self)
    if (len(self.game.players) == 0) and self.game.id in GameApp.games:
      del GameApp.games[self.game.id]
    self.game = None
    return reply

  @protocolmethod
  @errorBuffer
  @requireGame
  def gameStart(self):
    """Starts game associated with this connections """
    return self.game.start()

  @protocolmethod
  @errorBuffer
  @requireGame
  def gameStatus(self):
    """ Requests the status of your game """
    self.game.sendStatus([self])

  @protocolmethod
  @errorBuffer
  @requireTurn
  def endTurn(self):
    """ Attempts to end your turn """
    return self.game.nextTurn()
  
  # TODO Determine if this should have decorators
  def disconnect(self, reason):
    self.leaveGame()
   
  @protocolmethod
  @errorBuffer
  @requireTurn
  @requireTypes(None, int, str)
  def gameTalk(self, player, message):
    """Allows a player to display messages on the screen"""
    if self.game.turn is not self:
      return "Not your turn."
    return self.game.talk(player, message)

  @protocolmethod
  @errorBuffer
  @requireTurn
  @requireTypes(None, int, int, int, int)
  def gameOrbitalDrop(self, player, x, y, variant):
    """Allows a player to spawn a Droid."""
    if self.game.turn is not self:
      return "Not your turn."
    return self.game.orbitalDrop(player, x, y, variant)

  @protocolmethod
  @errorBuffer
  @requireTurn
  @requireTypes(None, int, int, int)
  def gameMove(self, droid, x, y):
    """Make the Droid move to the respective x and y location."""
    if self.game.turn is not self:
      return "Not your turn."
    return self.game.move(droid, x, y)

  @protocolmethod
  @errorBuffer
  @requireTurn
  @requireTypes(None, int, int, int)
  def gameOperate(self, droid, x, y):
    """Command to operate (repair, attack, hack) on another Droid."""
    if self.game.turn is not self:
      return "Not your turn."
    return self.game.operate(droid, x, y)


  @protocolmethod
  def whoami(self):
    """ Returns this connection's session identifiers """
    if self.name:
      return ("num", self.protocol.session_num), ("name", self.name)
    else:
      return ("num", self.protocol.session_num), ("name", "noone")

  @protocolmethod
  @requireLogin
  @requireTypes(None, str)
  def requestLog(self, logID):
    """ Requests a specific gamelog """ 
    global emptyLog
    
    # -arena in the command line means:
    # "nobody is ever going to see the log, don't send it, it's huge"
    if emptyLog:
      return ['log', logID, ""]
    
    with bz2.BZ2File("logs/" + logID + ".glog", "r") as infile:
      return ['log', logID, infile.read()]

  def writeSExpr(self, message):
    """ Adds backward compatibility with game logic written for the old
    server code
    """
    payload = sexpr2str(message)
    self.protocol.sendString(payload)

class TestGameServer(SexpProtocol):
  app = GameApp

emptyLog = False  

if __name__ == "__main__":
  import timer
  if '-notimeout' not in sys.argv:
    timer.install()
  portNumber = 19000
  if '-arena' in sys.argv:
    emptyLog = True
  if '-port' in sys.argv:
    indexNumber = sys.argv.index('-port') + 1
    portNumber = int(sys.argv[indexNumber])
  TestGameServer.main(portNumber)
