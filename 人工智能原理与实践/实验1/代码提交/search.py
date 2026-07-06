# search.py
# ---------
# Licensing Information:  You are free to use or extend these projects for
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
    Returns a sequence of moves that solves tinyMaze.  For any other maze, the
    sequence of moves will be incorrect, so only use this for tinyMaze.
    """
    from game import Directions
    s = Directions.SOUTH
    w = Directions.WEST
    return [s, s, w, s, w, w, s, w]

# --- 深度优先搜索 (Depth First Search, DFS) ---
def depthFirstSearch(problem):
    # 1. 初始化边界 (Fringe) - 使用栈 (Stack)
    search_fringe = util.Stack()
    
    # 节点存储格式: [状态 state, 路径成本 cost, 动作序列 path]
    start_node = [problem.getStartState(), 0, []]
    search_fringe.push(start_node)
    
    # 2. 初始化已访问/已关闭集合 (Closed Set)
    visited_states = []
    
    # 3. 循环直到边界为空
    while not search_fringe.isEmpty():
        # 弹出栈顶节点（LIFO，后进先出）
        current_state, current_cost, current_path = search_fringe.pop()
        
        # 4. 目标测试
        if problem.isGoalState(current_state):
            return current_path
            
        # 5. 扩展节点
        if current_state not in visited_states:
            visited_states.append(current_state)
            
            # 遍历所有后继状态 (successor, action, stepCost)
            for successor_state, action_to_successor, step_cost in problem.getSuccessors(current_state):
                # 计算新节点的总成本和路径
                new_total_cost = current_cost + step_cost
                new_path = current_path + [action_to_successor]
                
                # 将新节点推入栈中
                new_node = [successor_state, new_total_cost, new_path]
                search_fringe.push(new_node)
                
    return [] # 找不到路径

# --- 广度优先搜索 (Breadth First Search, BFS) ---
def breadthFirstSearch(problem):
    # 1. 初始化边界 (Fringe) - 使用队列 (Queue)
    search_fringe = util.Queue()
    
    # 节点存储格式: [状态 state, 路径成本 cost, 动作序列 path]
    start_node = [problem.getStartState(), 0, []]
    search_fringe.push(start_node)
    
    # 2. 初始化已访问/已关闭集合 (Closed Set)
    visited_states = []
    
    # 3. 循环直到边界为空
    while not search_fringe.isEmpty():
        # 弹出队首节点（FIFO，先进先出）
        current_state, current_cost, current_path = search_fringe.pop()
        
        # 4. 目标测试
        if problem.isGoalState(current_state):
            return current_path
            
        # 5. 扩展节点
        if current_state not in visited_states:
            visited_states.append(current_state)
            
            # 遍历所有后继状态
            for successor_state, action_to_successor, step_cost in problem.getSuccessors(current_state):
                # 计算新节点的总成本和路径
                new_total_cost = current_cost + step_cost
                new_path = current_path + [action_to_successor]
                
                # 将新节点推入队列中
                new_node = [successor_state, new_total_cost, new_path]
                search_fringe.push(new_node)
                
    return [] # 找不到路径

# --- 一致成本搜索 (Uniform Cost Search, UCS) ---
def uniformCostSearch(problem):
    # 1. 初始化边界 (Fringe) - 使用优先队列 (PriorityQueue)
    search_fringe = util.PriorityQueue()
    
    # 节点存储格式: [状态 state, 路径成本 g(n), 动作序列 path]
    start_node = [problem.getStartState(), 0, []]
    # 优先级 p = g(n) = 0
    start_priority = 0
    search_fringe.push(start_node, start_priority)
    
    # 2. 初始化已访问/已关闭集合 (Closed Set)
    # UCS 需要存储已访问状态及其到达的最小成本，但原代码只存储状态。
    # 为了保持逻辑不变，我们只记录状态，但这在图搜索中可能不是最优的。
    visited_states = [] 
    
    # 3. 循环直到边界为空
    while not search_fringe.isEmpty():
        # 弹出优先级最高的节点（成本最低）
        current_state, current_cost, current_path = search_fringe.pop()
        
        # 4. 目标测试
        if problem.isGoalState(current_state):
            return current_path
            
        # 5. 扩展节点
        if current_state not in visited_states:
            visited_states.append(current_state)
            
            # 遍历所有后继状态
            for successor_state, action_to_successor, step_cost in problem.getSuccessors(current_state):
                # 计算新节点的总成本 g(n')
                new_total_cost = current_cost + step_cost
                new_path = current_path + [action_to_successor]
                
                # 将新节点推入优先队列，优先级为 g(n')
                new_node = [successor_state, new_total_cost, new_path]
                search_fringe.push(new_node, new_total_cost)
                
    return [] # 找不到路径

def nullHeuristic(state, problem=None):
    """
    A heuristic function estimates the cost from the current state to the nearest
    goal in the provided SearchProblem.  This heuristic is trivial.
    """
    return 0

# --- A* 搜索 (A* Search) ---
def aStarSearch(problem, heuristic=nullHeuristic):
    # 1. 初始化边界 (Fringe) - 使用优先队列 (PriorityQueue)
    search_fringe = util.PriorityQueue()
    
    # 节点存储格式: [状态 state, 路径成本 g(n), 动作序列 path]
    start_state = problem.getStartState()
    start_cost = 0
    start_path = []
    
    # 优先级 p = f(n) = g(n) + h(n) = 0 + h(start_state)
    start_priority = start_cost + heuristic(start_state, problem)
    start_node = [start_state, start_cost, start_path]
    search_fringe.push(start_node, start_priority)
    
    # 2. 初始化已访问/已关闭集合 (Closed Set)
    visited_states = []
    
    # 3. 循环直到边界为空
    while not search_fringe.isEmpty():
        # 弹出优先级最高的节点 (f(n) 最小)
        current_state, current_cost_g, current_path = search_fringe.pop()
        
        # 4. 目标测试
        if problem.isGoalState(current_state):
            return current_path
            
        # 5. 扩展节点
        if current_state not in visited_states:
            visited_states.append(current_state)
            
            # 遍历所有后继状态
            for successor_state, action_to_successor, step_cost in problem.getSuccessors(current_state):
                # 计算新节点的路径成本 g(n')
                new_cost_g = current_cost_g + step_cost
                new_path = current_path + [action_to_successor]
                
                # 计算新节点的启发式值 h(n')
                new_heuristic_h = heuristic(successor_state, problem)
                
                # 计算新节点的总评估函数值 f(n') = g(n') + h(n')
                new_priority_f = new_cost_g + new_heuristic_h
                
                # 将新节点推入优先队列
                new_node = [successor_state, new_cost_g, new_path]
                search_fringe.push(new_node, new_priority_f)
                
    # 原代码中此处使用了 util.raiseNotDefined()，这里保持一致
    util.raiseNotDefined()

# Abbreviations
bfs = breadthFirstSearch
dfs = depthFirstSearch
astar = aStarSearch
ucs = uniformCostSearch