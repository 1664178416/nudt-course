# valueIterationAgents.py
# -----------------------
# Licensing Information:  You are free to use or extend these projects for
# educational purposes provided that (1) you do not distribute or publish
# solutions, (2) you retain this notice, and (3) you provide clear
# attribution to UC Berkeley, including a link to http://ai.berkeley.edu.
# 
# Attribution Information: The Pacman AI projects were developed at UC Berkeley.
# The core projects and autograders are primarily created by John DeNero
# (denero@cs.berkeley.edu) and Dan Klein (klein@cs.berkeley.edu).
# Student side autograding was added by Brad Miller, Nick Hay, and
# Pieter Abbeel (pabbeel@cs.berkeley.edu).


import mdp, util

from learningAgents import ValueEstimationAgent
import collections

class ValueIterationAgent(ValueEstimationAgent):
    """
        * Please read learningAgents.py before reading this.*

        A ValueIterationAgent takes a Markov decision process
        (see mdp.py) on initialization and runs value iteration
        for a given number of iterations using the supplied
        discount factor.
    """

    def __init__(self, mdp, discount=0.9, iterations=100):
        """
          Your value iteration agent should take an mdp on
          construction, run the indicated number of iterations
          and then act according to the resulting policy.

          Some useful mdp methods you will use:
              mdp.getStates()
              mdp.getPossibleActions(state)
              mdp.getTransitionStatesAndProbs(state, action)
              mdp.getReward(state, action, nextState)
              mdp.isTerminal(state)
        """
        self.mdp = mdp
        self.discount = discount
        self.iterations = iterations
        self.values = util.Counter() # A Counter is a dict with default 0
        self.runValueIteration()

    def runValueIteration(self):
        #  实现同步值迭代 (Synchronous Value Iteration)
        
        # 迭代指定的次数
        for current_iteration in range(self.iterations):
            # 复制当前的值函数，用于存储本次迭代的新值 V_{k+1}(s)
            updated_values = self.values.copy()
            
            # 遍历所有状态
            for current_state in self.mdp.getStates():
                # 终止状态的值固定为 0，跳过更新
                if self.mdp.isTerminal(current_state):
                    continue
                
                # 计算当前状态 V_{k+1}(s) = max_a Q_k(s, a)
                
                # 获取所有动作的 Q 值，并取最大值
                all_q_values = [self.getQValue(current_state, action)
                                for action in self.mdp.getPossibleActions(current_state)]
                
                # 更新新值字典
                if all_q_values:
                    updated_values[current_state] = max(all_q_values)
                # else: 如果状态没有合法动作（在非终止状态通常不会发生），保持原值不变
            
            # 用新计算的值更新 self.values，用于下一次迭代
            self.values = updated_values.copy()

    def getValue(self, state):
        """
          Return the value of the state (computed in __init__).
        """
        return self.values[state]

    def computeQValueFromValues(self, state, action):
        """
          Compute the Q-value of action in state from the
          value function stored in self.values.
          $Q(s, a) = \sum_{s'} T(s, a, s') [R(s, a, s') + \gamma V(s')]$
        """
        # 获取 (next_state, prob) 对的列表
        transitions = self.mdp.getTransitionStatesAndProbs(state, action)
        q_sum = 0
        
        # 遍历所有可能的 (下一个状态, 概率) 对
        for next_state, probability in transitions:
            # 立即奖励
            reward_val = self.mdp.getReward(state, action, next_state)
            
            # 折扣后的下一状态值
            next_value = self.getValue(next_state)
            discounted_term = self.discount * next_value
            
            # 期望值累加
            q_sum += probability * (reward_val + discounted_term)
            
        return q_sum

    def computeActionFromValues(self, state):
        """
          The policy is the best action in the given state
          according to the values currently stored in self.values.
          $\pi(s) = \arg\max_a Q(s, a)$

          You may break ties any way you see fit.  Note that if
          there are no legal actions, which is the case at the
          terminal state, you should return None.
        """
        # 如果是终止状态，没有动作，返回 None
        if self.mdp.isTerminal(state):
            return None
        
        # 使用 Counter 来存储 Q 值并找到最大值对应的动作
        q_value_map = util.Counter()
        
        # 遍历所有可能的动作
        for possible_action in self.mdp.getPossibleActions(state):
            q_value_map[possible_action] = self.getQValue(state, possible_action)

        # argMax() 返回具有最大值的键（动作），自动处理平局
        return q_value_map.argMax()

    def getPolicy(self, state):
        return self.computeActionFromValues(state)

    def getAction(self, state):
        "Returns the policy at the state (no exploration)."
        return self.computeActionFromValues(state)

    def getQValue(self, state, action):
        return self.computeQValueFromValues(state, action)

class AsynchronousValueIterationAgent(ValueIterationAgent):
    """
        * Please read learningAgents.py before reading this.*

        An AsynchronousValueIterationAgent takes a Markov decision process
        (see mdp.py) on initialization and runs cyclic value iteration
        for a given number of iterations using the supplied
        discount factor.
    """

    def __init__(self, mdp, discount=0.9, iterations=1000):
        """
          Your cyclic value iteration agent should take an mdp on
          construction, run the indicated number of iterations,
          and then act according to the resulting policy. Each iteration
          updates the value of only one state, which cycles through
          the states list. If the chosen state is terminal, nothing
          happens in that iteration.

          Some useful mdp methods you will use:
              mdp.getStates()
              mdp.getPossibleActions(state)
              mdp.getTransitionStatesAndProbs(state, action)
              mdp.getReward(state)
              mdp.isTerminal(state)
        """
        ValueIterationAgent.__init__(self, mdp, discount, iterations)

    def runValueIteration(self):
        #  实现异步值迭代：每次迭代更新一个状态，按顺序循环
        
        all_states = self.mdp.getStates()
        state_count = len(all_states)
        
        for iteration_index in range(self.iterations):
            # 确定本次迭代要更新的状态（循环索引）
            state_index = iteration_index % state_count
            state_to_update = all_states[state_index]
            
            # 如果是终止状态，跳过更新
            if self.mdp.isTerminal(state_to_update):
                continue
            
            # 计算该状态的最大 Q 值
            
            # 确保状态有合法动作
            possible_actions = self.mdp.getPossibleActions(state_to_update)
            if possible_actions:
                # 使用列表推导式找到 $\max_a Q(s, a)$
                max_q = max([self.computeQValueFromValues(state_to_update, action) 
                             for action in possible_actions])
                
                # 直接更新 self.values，这是异步迭代的关键
                self.values[state_to_update] = max_q

class PrioritizedSweepingValueIterationAgent(AsynchronousValueIterationAgent):
    """
        * Please read learningAgents.py before reading this.*

        A PrioritizedSweepingValueIterationAgent takes a Markov decision process
        (see mdp.py) on initialization and runs prioritized sweeping value iteration
        for a given number of iterations using the supplied parameters.
    """

    def __init__(self, mdp, discount=0.9, iterations=100, theta=1e-5):
        """
          Your prioritized sweeping value iteration agent should take an mdp on
          construction, run the indicated number of iterations,
          and then act according to the resulting policy.
        """
        self.theta = theta
        ValueIterationAgent.__init__(self, mdp, discount, iterations)

    def runValueIteration(self):
        #  实现优先权遍历值迭代 (Prioritized Sweeping)

        all_states = self.mdp.getStates()
        
        # 1. 预计算 Predecessors (前驱状态集合)
        # 存储所有 s' 的前驱状态集合：predecessor_map[s'] = {s1, s2, ...}
        predecessor_map = collections.defaultdict(set)
        
        for state_s in all_states:
            # 只有非终止状态才能作为前驱
            if self.mdp.isTerminal(state_s):
                continue
            
            for action_a in self.mdp.getPossibleActions(state_s):
                # 遍历所有可能的转移 (s', prob)
                for next_state_s_prime, probability in self.mdp.getTransitionStatesAndProbs(state_s, action_a):
                    if probability > 0:
                        predecessor_map[next_state_s_prime].add(state_s)

        # 2. 初始化优先队列 (PriorityQueue)
        priority_queue = util.PriorityQueue()
        
        # 遍历所有状态，计算初始差值并推入队列
        for state_s in all_states:
            if not self.mdp.isTerminal(state_s):
                # 计算 Bellman Error/Difference
                
                # 找到 $\max_a Q(s, a)$
                max_q_value = max([self.computeQValueFromValues(state_s, action_a) 
                                   for action_a in self.mdp.getPossibleActions(state_s)])
                
                # 计算差值 $|V(s) - \max_a Q(s, a)|$
                value_difference = abs(max_q_value - self.getValue(state_s))
                
                # 队列的优先级是负的差值 (因为 PriorityQueue 是最小堆)
                priority_queue.update(state_s, -value_difference)

        # 3. 循环迭代，执行优先级更新
        for iteration_step in range(self.iterations):
            # 如果队列为空，则收敛，退出循环
            if priority_queue.isEmpty():
                break

            # (A) 弹出优先级最高的 state
            state_to_process = priority_queue.pop()

            # (B) 更新当前状态的值
            if not self.mdp.isTerminal(state_to_process):
                # 重新计算并设置 $V(s) \leftarrow \max_a Q(s, a)$
                new_max_q = max([self.computeQValueFromValues(state_to_process, action_a)
                                 for action_a in self.mdp.getPossibleActions(state_to_process)])
                self.values[state_to_process] = new_max_q

            # (C) 遍历前驱状态并更新其优先级
            if state_to_process in predecessor_map:
                for predecessor_state in predecessor_map[state_to_process]:
                    
                    # 重新计算前驱状态的 $\max_a Q(pred, a)$
                    pred_max_q = max([self.computeQValueFromValues(predecessor_state, action_a) 
                                      for action_a in self.mdp.getPossibleActions(predecessor_state)])
                    
                    # 计算 Bellman Error/Difference
                    pred_difference = abs(pred_max_q - self.getValue(predecessor_state))
                    
                    # 如果差值大于阈值 $\theta$，则更新前驱状态在优先队列中的优先级
                    if pred_difference > self.theta:
                        priority_queue.update(predecessor_state, -pred_difference)