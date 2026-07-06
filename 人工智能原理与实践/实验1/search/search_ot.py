# search.py
# ---------
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


"""
In search.py, you will implement generic search algorithms which are called by
Pacman agents (in searchAgents.py).
"""

import util

class SearchProblem:
    """
    This class outlines the structure of a search problem, but doesn't implement
    any of the methods (in object-oriented terminology: an abstract class).

    You do not need to change anything in this class, ever.
    """

    def getStartState(self):
        """
        Returns the start state for the search problem.
        """
        util.raiseNotDefined()

    def isGoalState(self, state):
        """
          state: Search state

        Returns True if and only if the state is a valid goal state.
        """
        util.raiseNotDefined()

    def getSuccessors(self, state):
        """
          state: Search state

        For a given state, this should return a list of triples, (successor,
        action, stepCost), where 'successor' is a successor to the current
        state, 'action' is the action required to get there, and 'stepCost' is
        the incremental cost of expanding to that successor.
        """
        util.raiseNotDefined()

    def getCostOfActions(self, actions):
        """
         actions: A list of actions to take

        This method returns the total cost of a particular sequence of actions.
        The sequence must be composed of legal moves.
        """
        util.raiseNotDefined()


def tinyMazeSearch(problem):
    """
    Returns a sequence of moves that solves tinyMaze.  For any other maze, the
    sequence of moves will be incorrect, so only use this for tinyMaze.
    """
    from game import Directions
    s = Directions.SOUTH
    w = Directions.WEST
    return  [s, s, w, s, w, w, s, w]

def depthFirstSearch(problem):
    """
    Search the deepest nodes in the search tree first.

    Your search algorithm needs to return a list of actions that reaches the
    goal. Make sure to implement a graph search algorithm.

    To get started, you might want to try some of these simple commands to
    understand the search problem that is being passed in:

    print("Start:", problem.getStartState())
    print("Is the start a goal?", problem.isGoalState(problem.getStartState()))
    print("Start's successors:", problem.getSuccessors(problem.getStartState()))
    """
    "*** YOUR CODE HERE ***"
    """
        Search the deepest nodes in the search tree first.

        Your search algorithm needs to return a list of actions that reaches the
        goal. Make sure to implement a graph search algorithm.
        """
    frontier = util.Stack()
    frontier.push((problem.getStartState(), []))
    visited = set()

    while not frontier.isEmpty():
        state, actions = frontier.pop()

        # 提前检查是否已访问
        if state in visited:
            continue

        if problem.isGoalState(state):
            return actions

        visited.add(state)

        for next_state, action, cost in problem.getSuccessors(state):
            if next_state not in visited:  # 这里也要检查
                new_actions = actions + [action]
                frontier.push((next_state, new_actions))
    util.raiseNotDefined()

def breadthFirstSearch(problem):
    """Search the shallowest nodes in the search tree first."""
    "*** YOUR CODE HERE ***"
    """Search the shallowest nodes in the search tree first."""
    # 初始化队列用于BFS
    frontier = util.Queue()
    # 将起始状态和空路径加入队列
    frontier.push((problem.getStartState(), []))
    # 用于记录已访问状态的集合
    visited = set()

    while not frontier.isEmpty():
        # 从队列中取出当前状态和路径
        state, actions = frontier.pop()

        # 如果是目标状态，返回路径
        if problem.isGoalState(state):
            return actions

        # 如果还没有访问过这个状态
        if state not in visited:
            # 标记为已访问
            visited.add(state)

            # 获取所有后继状态并加入队列
            for next_state, action, cost in problem.getSuccessors(state):
                if next_state not in visited:
                    # 创建新路径：当前路径加上新动作
                    new_actions = actions + [action]
                    frontier.push((next_state, new_actions))

    # 如果没有找到解决方案，返回为：
    util.raiseNotDefined()

def uniformCostSearch(problem):
    """Search the node of least total cost first."""
    # 初始化优先队列用于UCS
    frontier = util.PriorityQueue()
    start_state = problem.getStartState()
    # 将起始状态、空路径和成本0加入优先队列，优先级为0
    frontier.push((start_state, [], 0), 0)
    # 用于记录已访问状态及其到达成本的字典
    visited = {}

    while not frontier.isEmpty():
        # 从优先队列中取出当前状态、路径和累计成本
        state, actions, cost = frontier.pop()

        # 如果是目标状态，返回路径
        if problem.isGoalState(state):
            return actions

        # 如果还没有访问过这个状态，或者找到了更便宜的路径
        if state not in visited or cost < visited[state]:
            # 记录访问状态和成本
            visited[state] = cost

            # 获取所有后继状态
            for next_state, action, step_cost in problem.getSuccessors(state):
                # 计算新的累计成本
                new_cost = cost + step_cost
                # 如果新状态未访问过，或者找到了更便宜的路径
                if next_state not in visited or new_cost < visited[next_state]:
                    new_actions = actions + [action]
                    # 优先级就是新的累计成本
                    frontier.push((next_state, new_actions, new_cost), new_cost)

    # 如果没有找到解决方案，返回空列表
    util.raiseNotDefined()

def nullHeuristic(state, problem=None):
    """
    A heuristic function estimates the cost from the current state to the nearest
    goal in the provided SearchProblem.  This heuristic is trivial.
    """
    return 0

def aStarSearch(problem, heuristic=nullHeuristic):
    """Search the node that has the lowest combined cost and heuristic first."""
    "*** YOUR CODE HERE ***"
    """Search the node that has the lowest combined cost and heuristic first."""
    # 初始化优先队列用于A*
    frontier = util.PriorityQueue()
    start_state = problem.getStartState()
    # 计算起始状态的启发式值
    start_heuristic = heuristic(start_state, problem)
    # 将起始状态、空路径、成本0加入队列，优先级为0+启发式值
    frontier.push((start_state, [], 0), 0 + start_heuristic)
    # 用于记录已访问状态及其到达成本的字典
    visited = {}

    while not frontier.isEmpty():
        # 从优先队列中取出当前状态、路径和累计成本
        state, actions, cost = frontier.pop()

        # 如果是目标状态，返回路径
        if problem.isGoalState(state):
            return actions

        # 如果还没有访问过这个状态，或者找到了更便宜的路径
        if state not in visited or cost < visited[state]:
            # 记录访问状态和成本
            visited[state] = cost

            # 获取所有后继状态
            for next_state, action, step_cost in problem.getSuccessors(state):
                # 计算新的累计成本
                new_cost = cost + step_cost
                # 如果新状态未访问过，或者找到了更便宜的路径
                if next_state not in visited or new_cost < visited[next_state]:
                    new_actions = actions + [action]
                    # 计算新状态的启发式值
                    new_heuristic = heuristic(next_state, problem)
                    # 优先级 = 累计成本 + 启发式值
                    priority = new_cost + new_heuristic
                    frontier.push((next_state, new_actions, new_cost), priority)

    # 如果没有找到解决方案，返回空列表
    util.raiseNotDefined()


# Abbreviations
bfs = breadthFirstSearch
dfs = depthFirstSearch
astar = aStarSearch
ucs = uniformCostSearch
