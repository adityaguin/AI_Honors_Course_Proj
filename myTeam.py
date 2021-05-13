# baselineTeam.py
# ---------------
# Licensing Information:  You are free to use or extend these projects for
# educational purposes provided that (1) you do not distribute or publish
# solutions, (2) you retain this notice, and (3) you provide clear
# attribution to UC Berkeley, including a link to http://ai.berkeley.edu.
#
# Attribution Information: The Pacman AI projects were developed at UC Berkeley.
# The core projects and autograders were primarily created by John DeNero
# (denero@cs.berkeley.edu) and Dan Klein (klein@cs.berkeley.edu).
# Student side autograding was added by Brad Miller, Nick Hay, and
# Pieter Abbeel (pabbeel@cs.berkeley.edu).


# baselineTeam.py
# ---------------
# Licensing Information: Please do not distribute or publish solutions to this
# project. You are free to use and extend these projects for educational
# purposes. The Pacman AI projects were developed at UC Berkeley, primarily by
# John DeNero (denero@cs.berkeley.edu) and Dan Klein (klein@cs.berkeley.edu).
# For more info, see http://inst.eecs.berkeley.edu/~cs188/sp09/pacman.html


# Not detecting that food is getting eaten
# Both agents just going into enemy territory; one should have gone lower and higher
# atm - replay 3
# atm - replay 5 (alpha didn't go for power pellet)
# atm - replay 7 (alpha agent wasn't scared of the ghosts, just went it)
# eid - replay 1 crashed

# Alpha agent prioritize vertical movement
# Instead of alpha getting worried all the time, compare the y values and then make it go for the food




from captureAgents import CaptureAgent
import distanceCalculator
import random, time, util, sys
from game import Directions
import game
from util import nearestPoint


#################
# Team creation #
#################

def createTeam(firstIndex, secondIndex, isRed,
               first='Alpha', second='Beta'):
  """
  This function should return a list of two agents that will form the
  team, initialized using firstIndex and secondIndex as their agent
  index numbers.  isRed is True if the red team is being created, and
  will be False if the blue team is being created.

  As a potentially helpful development aid, this function can take
  additional string-valued keyword arguments ("first" and "second" are
  such arguments in the case of this function), which will come from
  the --redOpts and --blueOpts command-line arguments to capture.py.
  For the nightly contest, however, your team will be created without
  any extra arguments, so you should make sure that the default
  behavior is what you want for the nightly contest.
  """
  return [eval(first)(firstIndex), eval(second)(secondIndex)]


##########
# Agents #
##########

class ReflexCaptureAgent(CaptureAgent):
  """
  A base class for reflex agents that chooses score-maximizing actions
  """

  def registerInitialState(self, gameState):
    self.start = gameState.getAgentPosition(self.index)
    CaptureAgent.registerInitialState(self, gameState)
    self.border = []
    borderColumn = gameState.data.layout.width / 2 - 1 if self.red else gameState.data.layout.width / 2
    borderHeight = gameState.data.layout.height
    for r in range(borderHeight):
      if not gameState.hasWall(borderColumn, r):
        self.border.append((borderColumn, r))
    teamIndices = self.getTeam(gameState)
    if teamIndices[0] != self.index:
      self.teamMate = teamIndices[0]
    else:
      self.teamMate = teamIndices[1]
    self.power = 0
    self.prevCapsules = []

  def randomAction(self, statecpy):
    actions = statecpy.getLegalActions(self.index)
    actions.remove(Directions.STOP)
    if len(actions) == 1:
      return actions[0]
    uglyReverse = Directions.REVERSE[statecpy.getAgentState(self.index).configuration.direction]
    if uglyReverse in actions:
      actions.remove(uglyReverse)
    return random.choice(actions)

  # def monteCarlo(self, nextSuccessor, depth):
  #     statecpy = nextSuccessor.deepCopy()
  #     for i in range(0, depth):
  #         statecpy = statecpy.generateSuccessor(self.index, self.randomAction(statecpy))
  #     return self.evaluate(statecpy, Directions.STOP)

  def chooseAction(self, gameState):
    """
    Picks among the actions with the highest Q(s,a).
    """
    currPosition = gameState.getAgentPosition(self.index)
    currFood = self.getFoodYouAreDefending(gameState).asList()
    partnerState = gameState.getAgentState(self.teamMate)
    # print(partnerState.configuration)
    if currPosition == self.goal or partnerState.getPosition() == self.goal:
      self.goal = None
    if len(currFood) < len(self.prevFood):
      eaten_food = set(self.prevFood) - set(currFood)
      # print(eaten_food)
      self.goal = eaten_food.pop()

    enemies = self.getOpponents(gameState)
    enemyStates = [gameState.getAgentState(e) for e in enemies]
    enemies_position = [a.getPosition() for a in enemyStates if a.isPacman and a.getPosition() != None]
    self.prevFood = self.getFoodYouAreDefending(gameState).asList()
    # print(enemies_position)
    # If we see an invader
    isEnemy = False
    if len(enemies_position) > 0:
      distances = [(self.getMazeDistance(currPosition, e), e) for e in enemies_position]
      minDist = 1000000000000
      close = 0
      for d in distances:
        if d[0] < minDist:
          minDist = d[0]
          close = d[1]
      isEnemy = True
      self.goal = close
    actions = gameState.getLegalActions(self.index)
    actions.remove(Directions.STOP)
    inEnemy = False
    if self.goal != None:
      inEnemy = self.goal[0] >= int(gameState.data.layout.width / 2 - 1) if self.red  else self.goal[0] <= int(gameState.data.layout.width / 2)
    if inEnemy:
      self.goal = None
    if gameState.getAgentState(self.index).scaredTimer != 0:
      self.goal = None
    # You can profile your evaluation time by uncommenting these lines
    # start = time.time()



    enemies_position = [self.getMazeDistance(a.getPosition(), currPosition)
                        for a in enemyStates if not a.isPacman and a.scaredTimer == 0 and a.getPosition() != None]
    enemyDistance = min(enemies_position) if len(enemies_position) > 0 else 100000
    scaredTimers = [a.scaredTimer for a in enemyStates]
    if (self.goal == None or gameState.getAgentState(self.index).isPacman):
      capsules = self.getCapsules(gameState)
      if len(capsules) > 0 and enemyDistance >= 5 and gameState.getAgentState(self.index).isPacman:
        # Gets power pellet
        self.power = scaredTimers[0] if scaredTimers[0] != 0 and scaredTimers[1] != 0 else 0
        self.prevCapsules = capsules
        pelletDist = [self.getMazeDistance(currPosition, c) for c in capsules]
        distToCapsule = min(pelletDist) if len(pelletDist) > 0 else -1
        # If distToCapsule
        for cap in capsules:
          if self.getMazeDistance(currPosition, cap) == distToCapsule:
            self.pellet = cap
        move_quality = []
        remove_actions = []
        avail_actions = gameState.getLegalActions(self.index)
        # self.Alpha = True
        # Alpha: 0.2 - 0.4
        # Beta: 0.6 - 0.8
        for action in avail_actions:
          successor = gameState.generateSuccessor(self.index, action)
          borderColumn = int(gameState.data.layout.width / 2 - 1) if self.red else int(gameState.data.layout.width / 2)
          new_pos = gameState.generateSuccessor(self.index, action).getAgentPosition(self.index)

          #self.patrolPoints = (firstPoint,secondPoint)
          distance = self.getMazeDistance(new_pos, self.pellet)
          if not (action == Directions.STOP or (action == Directions.REVERSE[gameState.getAgentState(self.index).configuration.direction])):
            move_quality.append(distance)
          elif len(remove_actions) < len(avail_actions) - 1:
            remove_actions.append(action)
          else:
            move_quality.append(distance)

        for action in remove_actions:
          avail_actions.remove(action)

        best_quality = min(move_quality)
        best_actions = []

        for idx, action in enumerate(avail_actions):
          if move_quality[idx] == best_quality:
            best_actions.append(action)

        return random.choice(best_actions)

      if enemyDistance < 5:
        rem_actions = []
        if len(actions) > 1:
          for ac in actions:
            # Check the successor
            successor = gameState.generateSuccessor(self.index, ac)
            succActions = successor.getLegalActions(self.index)
            succActions.remove(Directions.STOP)
            if len(succActions) == 1:
              rem_actions.append(ac)
          for ac in rem_actions:
            if len(actions) > 1:
              actions.remove(ac)






      values = [self.evaluate(gameState, a) for a in actions]
      valueAction = [(self.evaluate(gameState, a), a) for a in actions]
      # print("valueAction {}".format(valueAction))
      # print(values)
      # print 'eval time for agent %d: %.4f' % (self.index, time.time() - start)

      # maxValue = max(values)

      # bestActions = [a for a, v in zip(actions, values) if v == maxValue]
      # bestActions = []
      # values = []
      #  for a in actions:
      #      nextSuccessor = gameState.generateSuccessor(self.index, a)
      #      value = 0
      # for i in range(1, 2):
      #     # value += self.monteCarlo(nextSuccessor, 1)
      # values.append(value)
      maxValue = max(values)
      bestActions = [a for a, v in zip(actions, values) if v == maxValue]

      foodLeft = len(self.getFood(gameState).asList())
      return random.choice(bestActions)

      # if foodLeft <= 2:
      #     bestDist = 9999
      #     for action in actions:
      #         successor = self.getSuccessor(gameState, action)
      #         pos2 = successor.getAgentPosition(self.index)
      #         dist = self.getMazeDistance(self.start,pos2)
      #         if dist < bestDist:
      #             bestAction = action
      #             bestDist = dist
      #     return bestAction
      # print(gameState.getAgentPosition(self.teamMate))

    # ---------------------------------------------------------------#

    # print("Partner state is {}".format(partnerState))

    # Identifying the food

    # if self.goal == None: # ATTACK instead
    #     if currPosition in self.patrolPoints:
    #         if currPosition == self.patrolPoints[0]:
    #             self.goal = self.patrolPoints[1]
    #         else:
    #             self.goal = self.patrolPoints[0]
    #     else:
    #         self.goal = random.choice(self.patrolPoints)

    move_quality = []
    remove_actions = []
    avail_actions = gameState.getLegalActions(self.index)
    # self.Alpha = True
    # Alpha: 0.2 - 0.4
    # Beta: 0.6 - 0.8
    for action in avail_actions:
      successor = gameState.generateSuccessor(self.index, action)
      borderColumn = int(gameState.data.layout.width / 2 - 1) if self.red else int(gameState.data.layout.width / 2)
      new_pos = gameState.generateSuccessor(self.index, action).getAgentPosition(self.index)

      #self.patrolPoints = (firstPoint,secondPoint)
      distance = self.getMazeDistance(new_pos, self.goal)
      # Beta agent going after
      if self.isAlpha:
        if action == Directions.NORTH or action == Directions.SOUTH:
          distance -= 1
      # Check if enemy is nearby inside if statement
      if (gameState.getAgentState(self.index).scaredTimer == 0 or distance >= 3) and \
              not (successor.getAgentState(self.index).isPacman or action == Directions.STOP \
                   or (action == Directions.REVERSE[gameState.getAgentState(self.index).configuration.direction]) \
                   and gameState.getAgentState(self.index).scaredTimer == 0):
        move_quality.append(distance)
      elif len(remove_actions) < len(avail_actions) - 1:
        remove_actions.append(action)
      else:
        move_quality.append(distance)

    for action in remove_actions:
      avail_actions.remove(action)

    best_quality = min(move_quality)
    best_actions = []

    for idx, action in enumerate(avail_actions):
      if move_quality[idx] == best_quality:
        best_actions.append(action)

    return random.choice(best_actions)

  def getSuccessor(self, gameState, action):
    """
    Finds the next successor which is a grid position (location tuple).
    """
    successor = gameState.generateSuccessor(self.index, action)
    pos = successor.getAgentState(self.index).getPosition()
    if pos != nearestPoint(pos):
      # Only half a grid position was covered
      return successor.generateSuccessor(self.index, action)
    else:
      return successor

  def evaluate(self, gameState, action):
    """
    Computes a linear combination of features and feature weights
    """
    features = self.getFeatures(gameState, action)
    weights = self.getWeights(gameState, action)
    if self.isAlpha is False:
        print("{} * \n {} == {}".format(features, weights, features * weights))
        print("Direction: {}".format(action))
    return features * weights

  def getFeatures(self, gameState, action):
    """
    Returns a counter of features for the state
    """
    features = util.Counter()
    successor = self.getSuccessor(gameState, action)
    features['successorScore'] = self.getScore(successor)
    return features

  def getWeights(self, gameState, action):
    """
    Normally, weights do not depend on the gamestate.  They can be either
    a counter or a dictionary.
    """
    return {'successorScore': 1.0}


# RED IS ALPHA
# Not scared enough of enemy ghosts?
# Why didn't it go away from the ghosts?
class Alpha(ReflexCaptureAgent):
  """
  A reflex agent that seeks food. This is an agent
  we give you to get an idea of what an offensive agent might look like,
  but it is by no means the best or only way to build an offensive agent.
  """

  """
  A reflex agent that seeks food. This is an agent
  we give you to get an idea of what an offensive agent might look like,
  but it is by no means the best or only way to build an offensive agent.
  """

  def __init__(self, selfIndex):
    CaptureAgent.__init__(self, selfIndex)
    self.prevFood = []
    self.prevAttackFood = []
    self.numFoodEaten = 0
    self.goal = None
    self.isAlpha = True
    self.shouldReturn = False
    self.foodThreshhold = 4


  def getBestAction(self, gameState):
    pass
    # If distance(self, enemy) <= 5; retreat
    # if self.getMazeDistance
    # Else if prevFood is max length (decided by us), retreat regardless

    # Else eat nearest food possible

  def getFeatures(self, gameState, action):

    features = util.Counter()
    successor = self.getSuccessor(gameState, action)
    foodList = self.getFood(successor).asList()
    features['successorScore'] = self.getScore(successor)

    # Compute distance to the nearest food
    currPosition = successor.getAgentPosition(self.index)

    if len(foodList) > 0:  # This should always be True,  but better safe than sorry
      myPos = successor.getAgentState(self.index).getPosition()
      minDistance = min([self.getMazeDistance(myPos, food) for food in foodList])
      features['distanceToFood'] = minDistance
      # distance to nearest enemy

    enemyDistance = 100000
    enemies = self.getOpponents(gameState)
    enemyStates = [successor.getAgentState(e) for e in enemies]
    enemies_position = [self.getMazeDistance(a.getPosition(), currPosition)
                        for a in enemyStates if not a.isPacman and a.scaredTimer == 0 and a.getPosition() != None]

    scared_position = [a.scaredTimer for a in enemyStates if not a.isPacman and a.scaredTimer != 0 and a.getPosition() != None]
    # if len(scared_position) > 0:
    #   print(scared_position[0])

    enemyDistance = min(enemies_position) if len(enemies_position) > 0 else 100000
    enemyDistance = 100000 if enemyDistance > 5 else enemyDistance
    enemyDistance = 100000 if enemyDistance > 2 and not (
            gameState.getAgentState(self.index).isPacman or successor.getAgentState(
      self.index).isPacman) else enemyDistance
    # print(enemyDistance)
    features['distanceToEnemy'] = enemyDistance
    features['foodEaten'] = 0
    scaredTimers = [a.scaredTimer for a in enemyStates]
    # print("Self.scared time is {}".format(gameState.getAgentState(self.index).scaredTimer))
    # power = False
    capsules = self.getCapsules(gameState)
    # Gets power pellet
    self.power = scaredTimers[0] if scaredTimers[0] != 0 and scaredTimers[1] != 0 else 0
    self.prevCapsules = capsules
    # Check if both agents are scared, set timer equal to their scared timer
    self.shouldReturn = False
    if self.power > 0:
      self.foodThreshhold += gameState.getAgentState(self.index).numCarrying
    if gameState.getAgentState(self.index).numCarrying == 0:
      self.foodThreshhold = 4
    # if power == true, make self.power == 7, and if self.power == 7, then numcarrying
    if enemyDistance >= 100000 and (gameState.getAgentState(self.index).numCarrying < 3) or self.power > 0:
      self.shouldReturn = False
    elif (gameState.getAgentState(self.index).numCarrying >= 1):
      self.shouldReturn = True
    # if self.goal != None:
    #   self.shouldReturn = True

    # if self.
    self.prevAttackFood = self.getFood(gameState).asList()
    currFood = self.getFood(successor).asList()
    if len(self.prevAttackFood) > len(currFood) and enemyDistance > 4:
      self.numFoodEaten += 1
      features['foodEaten'] = 1
    smallBorderDistance = min([self.getMazeDistance(currPosition, borderPoint) for borderPoint in self.border])# \
    #     if gameState.getAgentState(self.index).numCarrying >= 1 or enemyDistance <= 5 else 0
    upper_y = int(0.80 * gameState.data.layout.height)
    small = 100000
    entry = None
    power = False
    self.goForPower = False

    # pelletDist = [self.getMazeDistance(currPosition, c) for c in capsules
    #               if self.getMazeDistance(currPosition, c) <= self.getMazeDistance(gameState.getAgentPosition(self.teamMate), c)]
    # distToCapsule = min(pelletDist) \
    #   if (len(capsules) > 0 and len(pelletDist) > 0) else 100009

    # if (enemyDistance != 100000 and distToCapsule <= smallBorderDistance) or (enemyDistance == 100000):
    #   if distToCapsule < 100009:
    #     self.goForPower = True
      # print("Power Pellet")
    # self.power -= 1 # Decrementing  regardless
    # Just to be safe here
    if self.power <= smallBorderDistance + 4 and self.power > 0:
      self.shouldReturn = True
    for borderpoint in self.border:
      if abs(borderpoint[1] - upper_y) < small:
        small = abs(borderpoint[1] - upper_y)
        entry = (borderpoint[0], borderpoint[1])
    prevPosition = gameState.getAgentPosition(self.index)
    # print("Alpha: {}".format(prevPosition))
    needsToEnter = currPosition[0] <= entry[0] if self.red else currPosition[0] >= entry[0]
    needsToEnter = needsToEnter and not gameState.getAgentState(self.index).isPacman #
    features['upper'] = self.getMazeDistance(currPosition, entry) if needsToEnter else 0
    features['borderDistance'] = smallBorderDistance
    # features['powerPelletDistance'] = distToCapsule
# Distance to power pellet or amount of food remaining
    return features

  def getWeights(self, gameState, action):
    borderWeight = gameState.getAgentState(self.index).numCarrying * -4
    # enemyWeight = 215 if not self.capsulePower else
    successor = gameState.generateSuccessor(self.index, action)
    # if successor.getAfe
    return {'successorScore': 500, 'distanceToFood': -8, 'distanceToEnemy': 400, 'foodEaten': 250,
            'borderDistance': -350 if self.shouldReturn else 0, 'upper': -20}

# Prioritize vertical movement over horizontal

class Beta(ReflexCaptureAgent):
  """
   A reflex agent that seeks food. This is an agent
   we give you to get an idea of what an offensive agent might look like,
   but it is by no means the best or only way to build an offensive agent.
   """

  """
  A reflex agent that seeks food. This is an agent
  we give you to get an idea of what an offensive agent might look like,
  but it is by no means the best or only way to build an offensive agent.
  """

  def __init__(self, selfIndex):
    CaptureAgent.__init__(self, selfIndex)
    self.prevFood = []
    self.numFoodEaten = 0
    self.goal = None
    self.prevAttackFood = []
    self.isAlpha = False
    self.shouldReturn = False

  def getBestAction(self, gameState):
    pass
    # If distance(self, enemy) <= 5; retreat
    # if self.getMazeDistance
    # Else if prevFood is max length (decided by us), retreat regardless

    # Else eat nearest food possible
  # Favor vertical traveling
  def getFeatures(self, gameState, action):
    features = util.Counter()
    successor = self.getSuccessor(gameState, action)
    foodList = self.getFood(successor).asList()
    features['successorScore'] = self.getScore(successor)  # self.getScore(successor)

    # Compute distance to the nearest food
    currPosition = successor.getAgentPosition(self.index)
    if len(foodList) > 0:  # This should always be True,  but better safe than sorry
      myPos = successor.getAgentState(self.index).getPosition()
      minDistance = min([self.getMazeDistance(myPos, food) for food in foodList])
      features['distanceToFood'] = minDistance
      # distance to nearest enemy

    enemyDistance = 100000
    enemies = self.getOpponents(gameState)
    enemyStates = [successor.getAgentState(e) for e in enemies]
    enemies_position = [self.getMazeDistance(a.getPosition(), currPosition)
                        for a in enemyStates if not a.isPacman and a.scaredTimer == 0 and a.getPosition() != None]

    enemyDistance = min(enemies_position) if len(enemies_position) > 0 else 100000
    enemyDistance = 0 if enemyDistance > 5 else enemyDistance
    enemyDistance = 0 if (enemyDistance > 3 or enemyDistance == 0) and not (
            gameState.getAgentState(self.index).isPacman or successor.getAgentState(
      self.index).isPacman) else enemyDistance
    # print(enemyDistance)
    features['distanceToEnemy'] = enemyDistance
    features['foodEaten'] = 0
    self.prevAttackFood = self.getFood(gameState).asList()
    currFood = self.getFood(successor).asList()
    # scaredTimers = [a.scaredTimer for a in enemyStates]
    # self.power = scaredTimers[0] if scaredTimers[0] != 0 and scaredTimers[1] != 0 else 0
    if len(self.prevAttackFood) > len(currFood):
      self.numFoodEaten += 1
      features['foodEaten'] = 1
    self.shouldReturn = False
    if enemyDistance == 0 and (gameState.getAgentState(self.index).numCarrying < 3):
      self.shouldReturn = False
    elif (gameState.getAgentState(self.index).numCarrying >= 1):
      self.shouldReturn = True
    # if self.goal != None:
    #   self.shouldReturn = True


    # smallBorderDistance = min([self.getMazeDistance(currPosition, borderPoint) for borderPoint in self.border])
    smallBorderDistance = min([self.getMazeDistance(currPosition, borderPoint) for borderPoint in self.border]) \
      if gameState.getAgentState(self.index).numCarrying >= 1 or enemyDistance <= 5 else 0
    lower_y = int(0.20 * gameState.data.layout.height)
    small = 100000
    entry = None

    self.goForPower = False
    # Get the CLOSEST capsule to go for
    capsules = self.getCapsules(gameState)
    distToCapsule = min([self.getMazeDistance(currPosition, c) for c in capsules]) if len(capsules) > 0 else 100009
    # for cap in capsules:
    #   distToCapsule = self.getMazeDistance(capsules[0], currPosition) if len(capsules) > 0 else 100009
    # distToCapsule = self.getMazeDistance(capsules[0], currPosition) if len(capsules) > 0 else 100009
    if (enemyDistance != 0 and distToCapsule <= smallBorderDistance) or (enemyDistance == 0):
      if distToCapsule < 100009:
        self.goForPower = True
        # self.shouldReturn = True
      #print("Power Pellet")

    for borderpoint in self.border:
      if abs(borderpoint[1] - lower_y) < small:
        small = abs(borderpoint[1] - lower_y)
        entry = (borderpoint[0], borderpoint[1])
    prevPosition = gameState.getAgentPosition(self.index)
    needsToEnter = currPosition[0] <= entry[0] if self.red else currPosition[0] >= entry[0]
    needsToEnter = needsToEnter and not gameState.getAgentState(self.index).isPacman
    #################################################################
    # print("Width: {}".format(gameState.data.layout.width))
    # if needsToEnter == False:
    #   if prevPosition[0] >= gameState.data.layout.width / 2:
    #     print("(WRONG) position: {}".format(prevPosition))
    # print needsToEnter, if needsToEnter is False, print it if printing false when enemy territory, WRONG
    ####################################################################
    features['lower'] = self.getMazeDistance(currPosition, entry) if needsToEnter else 0
    features['borderDistance'] = smallBorderDistance
    # features['powerPelletDistance'] = distToCapsule
    return features

  def getWeights(self, gameState, action):
    borderWeight = gameState.getAgentState(self.index).numCarrying * -10
    return {'successorScore': 500, 'distanceToFood': -3, 'distanceToEnemy': 250, 'foodEaten': 100,
            'borderDistance': -100 if self.shouldReturn else 0, 'lower': -10}
