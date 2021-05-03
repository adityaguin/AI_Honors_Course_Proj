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
        if self.goal == None or gameState.getAgentState(self.index).isPacman:
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
        for action in avail_actions:
            successor = gameState.generateSuccessor(self.index, action)
            borderColumn = int(gameState.data.layout.width / 2 - 1) if self.red else int(gameState.data.layout.width / 2)
            new_pos = gameState.generateSuccessor(self.index, action).getAgentPosition(self.index)
            distance = self.getMazeDistance(new_pos, self.goal)
            # Beta agent going after
            if self.isAlpha:
                if action == Directions.NORTH or action == Directions.SOUTH:
                    distance -= 1
            if (gameState.getAgentState(self.index).scaredTimer == 0 or distance >= 3) and\
                    not (successor.getAgentState(self.index).isPacman or action == Directions.STOP\
                    or (action == Directions.REVERSE[gameState.getAgentState(self.index).configuration.direction])\
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
        # if self.isAlpha is True:
        #     print("{} * {} == {}".format(features, weights, features * weights))
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
        features['successorScore'] = -len(foodList)  # self.getScore(successor)

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
        enemyDistance = 100000 if enemyDistance > 5 else enemyDistance
        enemyDistance = 100000 if enemyDistance > 2 and not (
                    gameState.getAgentState(self.index).isPacman or successor.getAgentState(
                self.index).isPacman) else enemyDistance
        # print(enemyDistance)
        features['distanceToEnemy'] = enemyDistance
        features['foodEaten'] = 0


        self.shouldReturn = False
        if self.goal != None or (gameState.getAgentState(self.index).numCarrying >= 1):
            self.shouldReturn = True
        if enemyDistance > 100000 and (gameState.getAgentState(self.index).numCarrying < 4):
            self.shouldReturn = False
        # if self.
        self.prevAttackFood = self.getFood(gameState).asList()
        currFood = self.getFood(successor).asList()
        if len(self.prevAttackFood) > len(currFood):
            self.numFoodEaten += 1
            features['foodEaten'] = 1
        smallBorderDistance = min([self.getMazeDistance(currPosition, borderPoint) for borderPoint in self.border])# \
        #     if gameState.getAgentState(self.index).numCarrying >= 1 or enemyDistance <= 5 else 0
        upper_y = int(0.80 * gameState.data.layout.height)
        small = 100000
        entry = None


        power = False
        capsules = self.getCapsules(gameState)
        distToCapsule = self.getMazeDistance(capsules[0], currPosition) if len(capsules) > 0 else 100009
        if enemyDistance < 100000 and distToCapsule <= smallBorderDistance:
            power = True
            # print("Power Pellet")

        for borderpoint in self.border:
            if abs(borderpoint[1] - upper_y) < small:
                small = abs(borderpoint[1] - upper_y)
                entry = (borderpoint[0], borderpoint[1])
        needsToEnter = currPosition[0] <= entry[0] if self.red else currPosition[0] >= entry[0]
        features['upper'] = self.getMazeDistance(currPosition, entry) if needsToEnter else 0
        features['borderDistance'] = smallBorderDistance if not power else distToCapsule
        return features

    def getWeights(self, gameState, action):
        borderWeight = gameState.getAgentState(self.index).numCarrying * -4
        # enemyWeight = 215 if not self.capsulePower else
        successor = gameState.generateSuccessor(self.index, action)
        # if successor.getAfe
        return {'successorScore': 10, 'distanceToFood': -8, 'distanceToEnemy': 300, 'foodEaten': 250,
                'borderDistance': -350 if self.shouldReturn else 0, 'upper': -10}


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
        features['successorScore'] = -len(foodList)  # self.getScore(successor)

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
        enemyDistance = 0 if enemyDistance > 2 and not (
                gameState.getAgentState(self.index).isPacman or successor.getAgentState(
            self.index).isPacman) else enemyDistance
        # print(enemyDistance)
        features['distanceToEnemy'] = enemyDistance
        features['foodEaten'] = 0
        self.prevAttackFood = self.getFood(gameState).asList()
        currFood = self.getFood(successor).asList()
        if len(self.prevAttackFood) > len(currFood):
            self.numFoodEaten += 1
            features['foodEaten'] = 1
        self.shouldReturn = False
        if self.goal != None or (gameState.getAgentState(self.index).numCarrying >= 1):
            self.shouldReturn = True
        if enemyDistance == 0 and (gameState.getAgentState(self.index).numCarrying < 4):
            self.shouldReturn = False

        # smallBorderDistance = min([self.getMazeDistance(currPosition, borderPoint) for borderPoint in self.border])
        smallBorderDistance = min([self.getMazeDistance(currPosition, borderPoint) for borderPoint in self.border]) \
            if gameState.getAgentState(self.index).numCarrying >= 1 or enemyDistance <= 5 else 0
        lower_y = int(0.20 * gameState.data.layout.height)
        small = 100000
        entry = None

        self.power = False
        capsules = self.getCapsules(gameState)
        distToCapsule = self.getMazeDistance(capsules[0], currPosition) if len(capsules) > 0 else 100009
        if enemyDistance != 0 and distToCapsule <= smallBorderDistance:
            self.power = True
            print("Power Pellet")

        for borderpoint in self.border:
            if abs(borderpoint[1] - lower_y) < small:
                small = abs(borderpoint[1] - lower_y)
                entry = (borderpoint[0], borderpoint[1])
        needsToEnter = currPosition[0] < entry[0] if self.red else currPosition[0] > entry[0]
        features['lower'] = self.getMazeDistance(currPosition, entry) if needsToEnter else 0
        features['borderDistance'] = smallBorderDistance if not self.power else distToCapsule
        return features

    def getWeights(self, gameState, action):
        borderWeight = gameState.getAgentState(self.index).numCarrying * -10
        return {'successorScore': 10, 'distanceToFood': -3, 'distanceToEnemy': 115 if not self.power else 50, 'foodEaten': 100,
                'borderDistance': -75 if self.shouldReturn else 0, 'lower': -50}
