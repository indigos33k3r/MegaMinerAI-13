#-*-python-*-
from BaseAI import BaseAI
from GameObject import *
from seastar import Seastar
from vexulizer.megaminer13 import DroidsVexulizer
        
TILE_WALL = 0
TILE_TURRET = 1
TILE_BASE = 2

UNIT_CLAW = 0
UNIT_ARCHER = 1 
UNIT_ENGINEER = 2
UNIT_HACKER = 3
UNIT_TURRET = 4 # This is a unit type?
UNIT_WALL = 5
UNIT_TERMINATOR = 6 
UNIT_HANGAR = 7

NEUTRAL_PLAYER = 2

class AI(BaseAI):
  """The class implementing gameplay logic."""
  @staticmethod
  def username():
    return "ActionBot"

  @staticmethod
  def password():
    return "HamSandwich"

  ##This function is called once, before your first turn
  def init(self):
    self.sea = Seastar(self.getMapWidth(),self.getMapHeight())
    self.vex = DroidsVexulizer(self,True)
    self.building = set()
    self.builditerator = None
    if self.getPlayerID() == 0:
        import buildorder0
        self.buildit = buildorder0.buildorder(self)
    if self.getPlayerID() == 1:
        import buildorder1
        self.buildit = buildorder1.buildorder(self)
    self.vtobuild = self.buildit.next()

  ##This function is called once, after your last turn
  def end(self):
    try:
        self.vex.end(self)
    except AttributeError:
        pass

  def validate(self):
    #With rigor, check properties
    for droid in self.droids:
        assert droid.getHealthLeft() <= droid.getMaxHealth()
        assert droid.getMovementLeft() <= droid.getMaxMovement()
        assert droid.getArmor() <= droid.getMaxArmor()
        assert droid.getAttacksLeft() <= droid.getMaxAttacks()
        assert droid.getMovementLeft() >= 0
        assert droid.getAttacksLeft() >= 0        

    for tile in self.tiles:
        #assert tile.getScrapAmount() > 0
        assert tile.getTurnsUntilAssembled() >= 0
        assert (tile.getOwner() == NEUTRAL_PLAYER and tile.getTurnsUntilAssembled() == 0) \
            or tile.owner != NEUTRAL_PLAYER

  def distance(self, c1, c2):
    return abs(c1[0]-c2[0])+abs(c1[1]-c2[1])

  def engineer_behavior(self, units, retreats=True):
    if len(units) == 0:
        return
    healing_targets = filter(lambda x: (x.getArmor() < x.getMaxArmor() or
                                        x.getHackets() > 0), self.mydroids_g+self.mybases)
    potential_targets = filter(lambda x: x.getVariant() != UNIT_ENGINEER, self.mydroids_g)
    retreats = retreats and len(healing_targets) > 0
    self.engage_objectives(units, healing_targets, potential_targets,
        within=units[0].getRange(), retreat_dance=retreats)

  def unit_only_behavior(self, units):
    if len(units) == 0:
        return

    primary_targets = filter(lambda x: x.getHealthLeft() > 0, self.enemycontrol)
    secondary_targets = [] 
    
    self.engage_objectives(units, primary_targets, secondary_targets, within=units[0].getRange())

  def unit_focused_behavior(self, units):
    if len(units) == 0:
        return

    primary_targets = filter(lambda x: x.getHealthLeft() > 0, self.enemycontrol)
    secondary_targets = filter(lambda x: x.getHealthLeft() > 0, self.enemybases) 
    
    self.engage_objectives(units, primary_targets, secondary_targets, within=units[0].getRange())
   
   
  def balanced_behavior(self, units, retreats=True):
    if len(units) == 0:
        return

    primary_targets = filter(lambda x: x.getHealthLeft() > 0 and x.getHackedTurnsLeft() == 0, self.enemyunits)
    secondary_targets = [] 
    
    self.engage_objectives(units, primary_targets, secondary_targets,
        within=units[0].getRange(),retreat_dance=retreats)
   
 
  def base_focused_behavior(self, units):
    if len(units) == 0:
        return

    primary_targets = filter(lambda x: x.getHealthLeft() > 0, self.enemybases) 
    secondary_targets = filter(lambda x: x.getHealthLeft() > 0, self.enemycontrol)
    
    self.engage_objectives(units, primary_targets, secondary_targets, within=units[0].getRange())
 
  def defense_focused_behavior(self, units):
    if len(units) == 0:
        return
    
    primary_targets = filter(lambda x: x.getHealthLeft() > 0 and
        x.getX() >= self.myhalf[0] and
        x.getX() <= self.myhalf[1], self.enemydroids)
    secondary_targets = filter(lambda x: x.getHealthLeft() > 0, self.enemydroids)

    self.engage_objectives(units, primary_targets, secondary_targets, within=units[0].getRange()) 

  def engage_objectives(self, units, primary, secondary, within=1, retreat_dance=True):
    tomove = {}
    if len(primary) == 0:
        primary = secondary
        secondary = []

    for unit in units:
        if unit.getMovementLeft() <= 0:
            continue
        if unit.getHealthLeft() <= 0:
            continue
        tomove[unit.getId()] = unit
    
    while len(tomove) > 0:
        starts = set([ (unit.getX(), unit.getY()) for (_,unit) in tomove.iteritems() ])
        ends = set([ (unit.getX(), unit.getY()) for unit in primary ])
        p = self.sea.get_path(starts,ends)
        if len(p) > 0:
            unit = self.unitsxy[p[0]]
            if unit.getHealthLeft() > 0:
                self.follow_path(unit,p,primary+secondary,within)
                self.update_state()
            tomove.pop(unit.getId(),None)
        else:
            # No unit can reach an objective
            break
    
    self.update_state()
    for unit in units:
        self.attack_set(unit, primary)
        self.attack_set(unit, secondary)
    self.update_state()

    if retreat_dance:
        tomove = {}
        for unit in units:
            if unit.getMovementLeft() <= 0:
                continue
            if unit.getHealthLeft() <= 0:
                continue
            tomove[unit.getId()] = unit

        while len(tomove) > 0:
            starts = [ (unit.getX(), unit.getY()) for (_,unit) in tomove.iteritems() ]
            ends = [ (unit.getX(), unit.getY()) for unit in self.mybases ]
            p = self.sea.get_path(starts,ends)
            if len(p) > 0:
                unit = self.unitsxy[p[0]]
                self.follow_path(unit,p,primary+secondary,within)
                self.update_state()
                tomove.pop(unit.getId(),None)
            else:
                # No unit can reach an objective
                break

    self.update_state()
 
        
 
  def follow_path(self, unit, path, operables, within):
    origpath = list(path)
    if len(path) == 0:
        return
    if path[0] == (unit.getX(), unit.getY()):
        path.pop(0)
    else:
        print "Path doesn't start with location"
        return
    for i in range(within):
        if len(path) == 0:
            return
        path.pop()
    for i in range(len(path)-1):
        assert(self.distance(path[i], path[i+1]) == 1)
    for step in path:
        if unit.getMovementLeft() <= 0:
            break
        d = self.distance(step,(unit.getX(),unit.getY()))
        if d != 1:
            print "Distance is {}".format(d)
            print "Bad Unit is"
            print unit
            break
        if not unit.move(step[0],step[1]): #Seastar should only yield good moves
            print "Moving Unit:"
            print unit
            print "Failed at {}".format(step)
            print "Path was:"
            for step2 in origpath:
                try:
                    contains = self.unitsxy[step2]
                except KeyError:
                    contains = "None"
                print "{} (Has {})".format(step2, contains) 
                if step2 == step:
                    break
            assert False        
        
        self.attack_set(unit,operables)

  def attack_set(self, unit, targets):
    starting_attacks = unit.getAttacksLeft()
    if len(targets) == 0:
        return
    if unit.getAttacksLeft() == 0:
        return
    targets = filter(lambda x: x.getHealthLeft() > 0 and
        1 <= self.distance( (x.getX(),x.getY()), (unit.getX(), unit.getY()) ) <= unit.getRange(), targets) 
    if len(targets) == 0:
        return
    targs = sorted(targets, key=lambda x: self.distance( (x.getX(),x.getY()), (unit.getX(), unit.getY()) ) )
    while unit.getAttacksLeft() > 0:
        result = 0
        for enemy in targs:
            if enemy.getHealthLeft() <= 0:
                continue
            if unit.getVariant() == UNIT_HACKER and (enemy.getHackets() >= enemy.getHacketsMax() or
                enemy.getHackedTurnsLeft() > 0):
                continue
            if unit.getAttacksLeft() == 0:
                break
            if not unit.operate(enemy.getX(), enemy.getY()):
                print "OPERATING FAILED:"
                print "attacker:"
                print unit
                print "Target:"
                print enemy
                assert False
            else:
                result += 1 
        if not result:
            return
  
  def update_state(self):
    # Player objects
    self.me = [ x for x in self.players if x.getId() == self.getPlayerID() ][0]
    self.myid = self.getPlayerID()
    self.enemy = [ x for x in self.players if x.getId() != self.getPlayerID()][0]
    self.enemyid = self.enemy.getId()
    assert self.myid != self.enemyid
    
    if self.myid == 0:
        self.myhalf = (0,self.getMapWidth()/2)
    else:
        self.myhalf = (self.getMapWidth()/2+1,self.getMapWidth())

    # My Droids
    self.myunits = [ x for x in self.droids if x.getOwner() == self.myid
        and x.getHealthLeft() > 0 ]
    self.mydroids = [ x for x in self.myunits if x.getVariant() != UNIT_HANGAR ]

    gf = lambda x: x.getHackedTurnsLeft() == 0
    hf = lambda x: x.getHackedTurnsLeft() > 0

    # Droids filter on hacked ness
    self.mydroids_g = filter(gf, self.mydroids)
    self.mydroids_h = filter(hf, self.mydroids)
   
    # Enemy Droids
    self.enemyunits = [ x for x in self.droids if x.getOwner() == self.enemyid
        and x.getHealthLeft() > 0 ]
    self.enemydroids = [ x for x in self.enemyunits if x.getVariant() != UNIT_HANGAR]

    # Droids filter on hacked ness
    self.enemydroids_g = filter(gf, self.enemydroids)
    self.enemydroids_h = filter(hf, self.enemydroids)

    self.mycontrol = self.mydroids_g + self.enemydroids_h
    self.enemycontrol = self.mydroids_h + self.enemydroids_g    

    # Units that can move
    mf = lambda x: x.getMaxMovement() > 0
    self.mymoveables = filter(mf, self.mycontrol)
    self.enemycontrol = filter(mf, self.enemycontrol)

    # Units that can't move.
    hf = lambda x: x.getTurnsToBeHacked() > 0 and x.getVariant() != UNIT_WALL
    self.enemyhackables = filter(hf, self.enemydroids)
    self.myhackables = filter(hf, self.mydroids)

    # Tiles
    self.mytiles = [ x for x in self.tiles if x.getOwner() == self.myid ]
    self.enemytiles = [ x for x in self.tiles if x.getOwner() == self.enemyid ]

    #Hangar Units
    wf = lambda x: x.getVariant() == UNIT_HANGAR
    self.mybases = filter(wf,self.myunits)
    self.enemybases = filter(wf,self.enemyunits)

    #Built walls
    wf = lambda x: x.getVariant() == UNIT_WALL
    self.mywalls = filter(wf, self.mydroids)
    self.enemywalls = filter(wf, self.enemydroids)

    #Built Turrets
    wf = lambda x: x.getVariant() == UNIT_TURRET
    self.myturrets = filter(wf, self.mydroids)
    self.enemyturrets = filter(wf, self.enemydroids)

    #Building wall tile
    wf = lambda x: x.getTurnsUntilAssembled() > 0 and x.getVariantToAssemble() == UNIT_WALL
    self.mywalls_b = filter(wf, self.mytiles)
    self.enemywalls_b = filter(wf, self.enemytiles)

    #Building (next turn)
    wf = lambda x: x.getTurnsUntilAssembled() == 1 and x.getVariantToAssemble() == UNIT_WALL
    self.mywalls_n = filter(wf, self.mytiles)
    self.enemywalls_n = filter(wf, self.enemytiles)
   
    #Building turret tile
    wf = lambda x: x.getTurnsUntilAssembled() > 0 and x.getVariantToAssemble() == UNIT_TURRET
    self.myturrets_b = filter(wf, self.mytiles)
    self.enemyturrets_b = filter(wf, self.enemytiles)

    #Building (next turn)
    wf = lambda x: x.getTurnsUntilAssembled() == 1 and x.getVariantToAssemble() == UNIT_TURRET
    self.myturrets_n = filter(wf, self.mytiles)
    self.enemyturrests_n = filter(wf, self.enemytiles) 

    # Neutral tiles
    self.opentiles = [ x for x in self.tiles if x.getTurnsUntilAssembled() == 0 ]
    self.droppingtiles = [ x for x in self.tiles if x.getTurnsUntilAssembled() > 0 ]
    self.nexttiles = [ x for x in self.tiles if x.getTurnsUntilAssembled() == 1 ]
    
    # Dicts, (x,y) -> tiles and units
    self.tilesxy = {}
    for tile in self.tiles:
        self.tilesxy[(tile.getX(),tile.getY())] = tile
    self.unitsxy = {}
    for unit in self.droids:
        if unit.getHealthLeft <= 0:
            continue
        self.unitsxy[(unit.getX(),unit.getY())] = unit

    # Seastar layers
    layers = {
    'MY_CONTROL':1,
    'ENEMY_CONTROL':2,
    'DROP_NEXT':4,
    'ENEMY_WALLS':8,
    'MY_WALLS':16,
    'ENEMY_TURRETS':128,
    'MY_TURRETS':256,
    'ENEMY_BASES':1024,
    'MY_BASES':2048,
    }

    # Bitwise or to combine layers into a mask
    BLOCKING = 0
    for k in layers:
        BLOCKING |= layers[k]
 
    self.sea.set_blocking(BLOCKING)
    self.sea.reset_obstacles()
    
    # Seastar: Add layers
    self.sea.add_mappables(self.myunits, layers['MY_CONTROL'])
    self.sea.add_mappables(self.enemyunits, layers['ENEMY_CONTROL'])    
    self.sea.add_mappables(self.nexttiles, layers['DROP_NEXT'])    
    self.sea.add_mappables(self.enemywalls, layers['ENEMY_WALLS'])    
    self.sea.add_mappables(self.mywalls, layers['MY_WALLS'])    
    self.sea.add_mappables(self.enemyturrets, layers['ENEMY_TURRETS'])    
    self.sea.add_mappables(self.myturrets, layers['MY_TURRETS'])    
    self.sea.add_mappables(self.enemybases, layers['ENEMY_BASES'])    
    self.sea.add_mappables(self.mybases, layers['MY_BASES'])

    #Push the game state into the vexulizer.
    self.vex.snapshot(self)
    

  ##This function is called each time it is your turn
  ##Return true to end your turn, return false to ask the server for updated information
  def run(self):
    self.update_state()

    print "Turn {}".format(self.getTurnNumber())

    # Mappables
    """
    REPORTED AS BUG 25
    assert len(self.mappables) > 0 # This was a problem in reef
    """

    # Before we start, check some stuff out, then continue.
    self.validate()    

    if False:
        """
        WORKING AT 3:26 4/2/2014
        """
        initial_scrap = self.me.getScrapAmount()
        # Validate that you can't spawn where another unit curently dropping
        for tile in self.droppingtiles:
            self.me.orbitalDrop(tile.getX(), tile.getY(), self.modelVariants[0].getVariant())
            assert initial_scrap == self.me.getScrapAmount()
            #assert tile.getTurnsUntilAssembled == 0
    
    """
    Reported in #20
    if False:
        #Validate you can't drop base tiles
        for tile in self.opentiles:
            self.me.orbitalDrop(tile.getX(), tile.getY(), UNIT_HANGAR)
            assert tile.getTurnsUntilAssembled == 0
    """

    print "Spawning Units"
    self.building = set()
    spawnpts = list(self.opentiles)

    while 1:
        variant = filter(lambda x: x.getVariant() == self.vtobuild[0], self.modelVariants)[0]
        
        if self.vtobuild[1] == None:
            if self.myid == 0:
                spawntarget = (0, self.getMapHeight()/2)
            else:
                spawntarget = (self.getMapWidth()-1, self.getMapHeight()/2)
        else:
            spawntarget = self.vtobuild[1]
        spawnpts.sort(key=lambda x: (abs(spawntarget[0]-x.getX()), abs(spawntarget[1]-x.getY()))  )
        
        if self.me.getScrapAmount() < variant.getCost():
            break

        print "Building {0}".format(self.vtobuild)
        #Simple AI, pick a unit type, (Other than hangar), and drop those
        for tile in spawnpts:
            if (tile.getX(), tile.getY()) in self.unitsxy:
                continue
            if (tile.getX(), tile.getY()) in self.building:
                continue
            #If we've made it this far, we can spawn the variant
            initial_scrap = self.me.getScrapAmount()
            self.me.orbitalDrop(tile.getX(), tile.getY(), variant.getVariant())
            self.building.add( (tile.getX(), tile.getY()) )
            assert initial_scrap > self.me.getScrapAmount()
            break
        self.vtobuild = self.buildit.next()

    self.update_state()
    
    """
    UNIT_CLAW = 0
    UNIT_ARCHER = 1 
    UNIT_ENGINEER = 2
    UNIT_HACKER = 3
    UNIT_TURRET = 4 # This is a unit type?
    UNIT_WALL = 5
    UNIT_TERMINATOR = 6 
    UNIT_HANGAR = 7
    """
 
    hackers = filter(lambda x: x.getVariant() == UNIT_HACKER, self.mycontrol)
    engineers = filter(lambda x: x.getVariant() == UNIT_ENGINEER, self.mycontrol)
    claws = filter(lambda x: x.getVariant() == UNIT_CLAW, self.mycontrol)
    archers = filter(lambda x: x.getVariant() == UNIT_ARCHER, self.mycontrol)
    turrets = filter(lambda x: x.getVariant() == UNIT_TURRET, self.mycontrol)
    terminators = filter(lambda x: x.getVariant() == UNIT_TERMINATOR, self.mycontrol)

    self.update_state()
    self.engineer_behavior(engineers)
    self.balanced_behavior(claws)
    self.balanced_behavior(archers)
    self.balanced_behavior(terminators, retreats=True)
    self.unit_only_behavior(hackers)
    self.balanced_behavior(turrets)

    print "Finished"
    return 1

  def __init__(self, conn):
    BaseAI.__init__(self, conn)
