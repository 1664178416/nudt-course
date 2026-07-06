# multiAgents.py
# --------------
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


from util import manhattanDistance
from game import Directions
import random, util

from game import Agent

class ReflexAgent(Agent):
    """
    A reflex agent chooses an action at each choice point by examining
    its alternatives via a state evaluation function.

    The code below is provided as a guide.  You are welcome to change
    it in any way you see fit, so long as you don't touch our method
    headers.
    """


    def getAction(self, gameState):
        """
        You do not need to change this method, but you're welcome to.

        getAction chooses among the best options according to the evaluation function.

        Just like in the previous project, getAction takes a GameState and returns
        some Directions.X for some X in the set {NORTH, SOUTH, WEST, EAST, STOP}
        """
        # Collect legal moves and successor states
        legalMoves = gameState.getLegalActions()

        # Choose one of the best actions
        scores = [self.evaluationFunction(gameState, action) for action in legalMoves]
        bestScore = max(scores)
        bestIndices = [index for index in range(len(scores)) if scores[index] == bestScore]
        chosenIndex = random.choice(bestIndices) # Pick randomly among the best

        "Add more of your code here if you want to"

        return legalMoves[chosenIndex]

    def evaluationFunction(self, currentGameState, action):
        """
        Design a better evaluation function here.

        The evaluation function takes in the current and proposed successor
        GameStates (pacman.py) and returns a number, where higher numbers are better.

        The code below extracts some useful information from the state, like the
        remaining food (newFood) and Pacman position after moving (newPos).
        newScaredTimes holds the number of moves that each ghost will remain
        scared because of Pacman having eaten a power pellet.

        Print out these variables to see what you're getting, then combine them
        to create a masterful evaluation function.
        """
        # Useful information you can extract from a GameState (pacman.py)
        successorGameState = currentGameState.generatePacmanSuccessor(action)
        newPos = successorGameState.getPacmanPosition()
        newFood = successorGameState.getFood()
        newGhostStates = successorGameState.getGhostStates()
        newScaredTimes = [ghostState.scaredTimer for ghostState in newGhostStates]

        "*** YOUR CODE HERE ***"
        # 转换为列表便于处理
        food_list = newFood.asList()
        ghost_positions = [ghost.getPosition() for ghost in newGhostStates]
        
        # 获取当前的恐慌状态 (逻辑保持原样，只取第一个)
        is_scared = newScaredTimes[0] > 0

        # 1. 检查是否撞到幽灵（非恐慌状态）
        if not is_scared and (newPos in ghost_positions):
            return -1.0

        # 2. 检查是否吃到食物
        if newPos in currentGameState.getFood().asList():
            return 1.0

        # 3. 计算距离最近的食物和幽灵
        # 注意：此处逻辑假设 food_list 和 ghost_positions 非空，保留原逻辑
        closest_food_dist = min([util.manhattanDistance(f, newPos) for f in food_list])
        closest_ghost_dist = min([util.manhattanDistance(g, newPos) for g in ghost_positions])

        # 4. 返回评分公式：(1/最近食物距离) - (1/最近幽灵距离)
        return (1.0 / closest_food_dist) - (1.0 / closest_ghost_dist)

def scoreEvaluationFunction(currentGameState):
    """
    This default evaluation function just returns the score of the state.
    The score is the same one displayed in the Pacman GUI.

    This evaluation function is meant for use with adversarial search agents
    (not reflex agents).
    """
    return currentGameState.getScore()

class MultiAgentSearchAgent(Agent):
    """
    This class provides some common elements to all of your
    multi-agent searchers.  Any methods defined here will be available
    to the MinimaxPacmanAgent, AlphaBetaPacmanAgent & ExpectimaxPacmanAgent.

    You *do not* need to make any changes here, but you can if you want to
    add functionality to all your adversarial search agents.  Please do not
    remove anything, however.

    Note: this is an abstract class: one that should not be instantiated.  It's
    only partially specified, and designed to be extended.  Agent (game.py)
    is another abstract class.
    """

    def __init__(self, evalFn = 'scoreEvaluationFunction', depth = '2'):
        self.index = 0 # Pacman is always agent index 0
        self.evaluationFunction = util.lookup(evalFn, globals())
        self.depth = int(depth)

class MinimaxAgent(MultiAgentSearchAgent):
    """
    Your minimax agent (question 2)
    """

    def getAction(self, gameState):
        """
        Returns the minimax action from the current gameState using self.depth
        and self.evaluationFunction.
        """
        "*** YOUR CODE HERE ***"
        
        # 内部函数：检查是否是终止状态
        def is_terminal(state, depth):
            return state.isWin() or state.isLose() or depth == self.depth

        # 内部函数：Min层 (幽灵)
        def minimize(state, depth, agent_index):
            if is_terminal(state, depth):
                return self.evaluationFunction(state)

            value = float('inf')
            legal_actions = state.getLegalActions(agent_index)
            
            # 获取下一个代理的索引（如果是最后一个幽灵，则下一个是Pacman）
            next_agent = agent_index + 1
            num_agents = state.getNumAgents()

            for action in legal_actions:
                successor = state.generateSuccessor(agent_index, action)
                if next_agent == num_agents:
                    # 最后一个幽灵行动后，深度+1，轮到Pacman (agent 0)
                    value = min(value, maximize(successor, depth + 1))
                else:
                    # 下一个幽灵行动，深度不变
                    value = min(value, minimize(successor, depth, next_agent))
            return value

        # 内部函数：Max层 (Pacman)
        def maximize(state, depth):
            if is_terminal(state, depth):
                return self.evaluationFunction(state)

            value = float('-inf')
            legal_actions = state.getLegalActions(0)

            for action in legal_actions:
                # Pacman行动后，轮到第一个幽灵 (agent 1)
                successor = state.generateSuccessor(0, action)
                value = max(value, minimize(successor, depth, 1))
            return value

        # 根节点逻辑：选择最佳动作
        best_action = Directions.STOP
        max_val = float('-inf')
        
        for action in gameState.getLegalActions(0):
            val = minimize(gameState.generateSuccessor(0, action), 0, 1)
            if val > max_val:
                max_val = val
                best_action = action
                
        return best_action

class AlphaBetaAgent(MultiAgentSearchAgent):
    """
    Your minimax agent with alpha-beta pruning (question 3)
    """

    def getAction(self, gameState):
        """
        Returns the minimax action using self.depth and self.evaluationFunction
        """
        "*** YOUR CODE HERE ***"
        
        # 通用递归搜索函数，整合了 Max 和 Min 的逻辑
        def alpha_beta_search(state, depth, agent_index, alpha, beta):
            # 终止条件：达到深度、胜利或失败
            if depth == self.depth or state.isWin() or state.isLose():
                return self.evaluationFunction(state)

            # Max层：Pacman (agent_index == 0)
            if agent_index == 0:
                value = float('-inf')
                for action in state.getLegalActions(agent_index):
                    successor = state.generateSuccessor(agent_index, action)
                    # Pacman之后是第一个幽灵(1)，深度不变
                    value = max(value, alpha_beta_search(successor, depth, 1, alpha, beta))
                    if value > beta:
                        return value
                    alpha = max(alpha, value)
                return value
            
            # Min层：幽灵 (agent_index > 0)
            else:
                value = float('inf')
                next_agent = agent_index + 1
                num_agents = state.getNumAgents()
                
                for action in state.getLegalActions(agent_index):
                    successor = state.generateSuccessor(agent_index, action)
                    
                    if next_agent == num_agents:
                        # 最后一个幽灵走完，回到Pacman(0)，深度+1
                        value = min(value, alpha_beta_search(successor, depth + 1, 0, alpha, beta))
                    else:
                        # 下一个幽灵，深度不变
                        value = min(value, alpha_beta_search(successor, depth, next_agent, alpha, beta))
                    
                    if value < alpha:
                        return value
                    beta = min(beta, value)
                return value

        # 根节点执行逻辑
        best_action = Directions.STOP
        current_value = float('-inf')
        alpha = float('-inf')
        beta = float('inf')

        for action in gameState.getLegalActions(0):
            successor = gameState.generateSuccessor(0, action)
            # 根节点是Pacman，下一步是agent 1
            value = alpha_beta_search(successor, 0, 1, alpha, beta)
            
            if value > current_value:
                current_value = value
                best_action = action
            
            # 更新根节点的 alpha
            alpha = max(alpha, current_value)
            
        return best_action

class ExpectimaxAgent(MultiAgentSearchAgent):
    """
      Your expectimax agent (question 4)
    """

    def getAction(self, gameState):
        """
        Returns the expectimax action using self.depth and self.evaluationFunction

        All ghosts should be modeled as choosing uniformly at random from their
        legal moves.
        """
        "*** YOUR CODE HERE ***"

        def expectimax_search(state, depth, agent_index):
            # 终止条件
            if depth == self.depth or state.isWin() or state.isLose():
                return self.evaluationFunction(state)

            num_agents = state.getNumAgents()
            legal_actions = state.getLegalActions(agent_index)
            
            # Max节点 (Pacman)
            if agent_index == 0:
                current_max = float('-inf')
                for action in legal_actions:
                    successor = state.generateSuccessor(agent_index, action)
                    current_max = max(current_max, expectimax_search(successor, depth, 1))
                return current_max
            
            # Chance节点 (Ghosts) - 计算平均值
            else:
                total_value = 0.0
                next_agent = agent_index + 1
                
                for action in legal_actions:
                    successor = state.generateSuccessor(agent_index, action)
                    if next_agent == num_agents:
                        # 最后一个幽灵，下一步回到Pacman，深度+1
                        total_value += expectimax_search(successor, depth + 1, 0)
                    else:
                        # 下一个幽灵
                        total_value += expectimax_search(successor, depth, next_agent)
                
                return total_value / len(legal_actions)

        # 根节点逻辑
        best_action = Directions.STOP
        max_value = float('-inf')

        for action in gameState.getLegalActions(0):
            successor = gameState.generateSuccessor(0, action)
            value = expectimax_search(successor, 0, 1)
            if value > max_value:
                max_value = value
                best_action = action
        
        return best_action

def betterEvaluationFunction(currentGameState):
    """
    Your extreme ghost-hunting, pellet-nabbing, food-gobbling, unstoppable
    evaluation function (question 5).
    """
    "*** YOUR CODE HERE ***"
    pacman_pos = currentGameState.getPacmanPosition()
    food_grid = currentGameState.getFood()
    ghost_states = currentGameState.getGhostStates()

    # 常量定义
    INF_VALUE = 1e8
    WEIGHT_FOOD = 10.0
    WEIGHT_GHOST = -10.0
    WEIGHT_SCARED_GHOST = 100.0

    score = currentGameState.getScore()

    # 1. 评估食物距离
    food_list = food_grid.asList()
    if food_list:
        dist_to_food = [util.manhattanDistance(pacman_pos, food) for food in food_list]
        # 加上最近食物距离的倒数权重
        score += WEIGHT_FOOD / min(dist_to_food)
    else:
        score += WEIGHT_FOOD

    # 2. 评估幽灵距离
    for ghost in ghost_states:
        dist_to_ghost = manhattanDistance(pacman_pos, ghost.getPosition())
        
        if dist_to_ghost > 0:
            if ghost.scaredTimer > 0:
                # 幽灵恐慌，鼓励靠近
                score += WEIGHT_SCARED_GHOST / dist_to_ghost
            else:
                # 幽灵正常，鼓励远离
                score += WEIGHT_GHOST / dist_to_ghost
        else:
            # 距离为0，被抓，返回极小值
            return -INF_VALUE

    return score

# Abbreviation
better = betterEvaluationFunction