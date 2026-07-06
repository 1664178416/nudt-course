# qlearningAgents.py
# ------------------
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


from game import *
from learningAgents import ReinforcementAgent
from featureExtractors import *

import random, util, math

class QLearningAgent(ReinforcementAgent):
    """
      Q-Learning Agent

      Functions you should fill in:
        - computeValueFromQValues
        - computeActionFromQValues
        - getQValue
        - getAction
        - update

      Instance variables you have access to
        - self.epsilon (exploration prob)
        - self.alpha (learning rate)
        - self.discount (discount rate)

      Functions you should use
        - self.getLegalActions(state)
          which returns legal actions for a state
    """
    def __init__(self, **args):
        "You can initialize Q-values here..."
        ReinforcementAgent.__init__(self, **args)

        # 存储 Q(s, a) 值，使用 util.Counter（字典，默认值为 0.0）
        self.q_table = util.Counter()

    def getQValue(self, state, action):
        """
          Returns Q(state,action)
          Should return 0.0 if we have never seen a state
          or the Q node value otherwise
        """
        # Q 值存储为键值对 (state, action)
        return self.q_table[(state, action)]


    def computeValueFromQValues(self, state):
        """
          Returns max_action Q(state,action)
          where the max is over legal actions.  Note that if
          there are no legal actions, which is the case at the
          terminal state, you should return a value of 0.0.
        """
        legal_actions = self.getLegalActions(state)
        # 如果是终止状态，没有合法动作，则返回 0.0
        if not legal_actions:
            return 0.0
            
        # 寻找 Q(s, a) 中的最大值
        max_q = float('-inf')
        for action in legal_actions:
            q_value = self.getQValue(state, action)
            max_q = max(max_q, q_value)
            
        return max_q

    def computeActionFromQValues(self, state):
        """
          Compute the best action to take in a state.  Note that if there
          are no legal actions, which is the case at the terminal state,
          you should return None.
        """
        legal_actions = self.getLegalActions(state)
        # 终止状态返回 None
        if not legal_actions:
            return None
            
        # 找到当前状态的最大 Q 值 V(s) = max_a Q(s, a)
        optimal_q_value = self.computeValueFromQValues(state)
        
        # 收集所有 Q 值等于最大 Q 值的动作（处理平局）
        optimal_actions = []
        for action in legal_actions:
            if optimal_q_value == self.getQValue(state, action): 
                optimal_actions.append(action) 
                
        # 从最优动作列表中随机选择一个
        return random.choice(optimal_actions)

    def getAction(self, state):
        """
          Compute the action to take in the current state.  With
          probability self.epsilon, we should take a random action and
          take the best policy action otherwise.  Note that if there are
          no legal actions, which is the case at the terminal state, you
          should choose None as the action.

          HINT: You might want to use util.flipCoin(prob)
          HINT: To pick randomly from a list, use random.choice(list)
        """
        # Pick Action
        legal_actions = self.getLegalActions(state)
        
        # 终止状态处理
        if not legal_actions:
            return None
            
        chosen_action = None
        
        # epsilon-greedy 策略：以 $\epsilon$ 概率探索 (随机动作)
        if util.flipCoin(self.epsilon):
            chosen_action = random.choice(legal_actions)
        # 以 $1-\epsilon$ 概率利用 (最优动作)
        else:
            chosen_action = self.getPolicy(state)
            
        return chosen_action

    def update(self, state, action, nextState, reward):
        """
          The parent class calls this to observe a
          state = action => nextState and reward transition.
          You should do your Q-Value update here

          NOTE: You should never call this function,
          it will be called on your behalf
        """
        # Q-Learning 更新规则：
        # $Q(s, a) \leftarrow (1-\alpha) Q(s, a) + \alpha \cdot [R(s, a, s') + \gamma \max_{a'} Q(s', a')]$
        
        # 1. 估算新值 (样本): $R(s, a, s') + \gamma \max_{a'} Q(s', a')$
        max_q_next_state = self.computeValueFromQValues(nextState) # $\max_{a'} Q(s', a')$
        sample_value = reward + (self.discount * max_q_next_state) 
        
        # 2. 当前 Q 值
        current_q_value = self.q_table[(state, action)]
        
        # 3. 更新 Q 值
        updated_q_value = (1.0 - self.alpha) * current_q_value + self.alpha * sample_value 
        
        self.q_table[(state, action)] = updated_q_value

    def getPolicy(self, state):
        return self.computeActionFromQValues(state)

    def getValue(self, state):
        return self.computeValueFromQValues(state)


class PacmanQAgent(QLearningAgent):
    "Exactly the same as QLearningAgent, but with different default parameters"

    def __init__(self, epsilon=0.05, gamma=0.8, alpha=0.2, numTraining=0, **args):
        """
        These default parameters can be changed from the pacman.py command line.
        For example, to change the exploration rate, try:
            python pacman.py -p PacmanQLearningAgent -a epsilon=0.1

        alpha     - learning rate
        epsilon   - exploration rate
        gamma     - discount factor
        numTraining - number of training episodes, i.e. no learning after these many episodes
        """
        args['epsilon'] = epsilon
        args['gamma'] = gamma
        args['alpha'] = alpha
        args['numTraining'] = numTraining
        self.index = 0  # This is always Pacman
        QLearningAgent.__init__(self, **args)

    def getAction(self, state):
        """
        Simply calls the getAction method of QLearningAgent and then
        informs parent of action for Pacman.  Do not change or remove this
        method.
        """
        action = QLearningAgent.getAction(self, state)
        self.doAction(state, action)
        return action


class ApproximateQAgent(PacmanQAgent):
    """
        ApproximateQLearningAgent

        You should only have to overwrite getQValue
        and update.  All other QLearningAgent functions
        should work as is.
    """

    def __init__(self, extractor='IdentityExtractor', **args):
        self.featExtractor = util.lookup(extractor, globals())()
        PacmanQAgent.__init__(self, **args)
        self.weights = util.Counter()

    def getWeights(self):
        return self.weights

    def getQValue(self, state, action):
        """
          Should return Q(state,action) = w * featureVector
          where * is the dotProduct operator
          $Q(s, a) = \sum_i w_i f_i(s, a)$
        """
        # $w \cdot f(s, a)$ 即为 self.weights * self.featExtractor.getFeatures(state, action)
        feature_vector = self.featExtractor.getFeatures(state, action)
        return self.getWeights() * feature_vector

    def update(self, state, action, nextState, reward):
        """
          Should update your weights based on transition
          $w_i \leftarrow w_i + \alpha \cdot \text{difference} \cdot f_i(s, a)$
        """
        # 计算时序差分 (Temporal Difference, TD) 误差:
        # $\text{difference} = [R(s, a, s') + \gamma \max_{a'} Q(s', a')] - Q(s, a)$
        
        # 1. 估算新值: $R(s, a, s') + \gamma \max_{a'} Q(s', a')$
        estimated_next_value = reward + self.discount * self.computeValueFromQValues(nextState)
        
        # 2. 当前 Q 值: $Q(s, a)$
        current_q_value = self.getQValue(state, action)
        
        # 3. 计算 TD 误差
        td_error = estimated_next_value - current_q_value
        
        # 4. 获取特征向量
        features = self.featExtractor.getFeatures(state, action)

        # 5. 更新权重 $w_i$
        # $w_i \leftarrow w_i + \alpha \cdot \text{td\_error} \cdot f_i(s, a)$
        for feature_name, feature_value in features.items():
            # feature_value 即为 $f_i(s, a)$
            # self.weights[feature_name] 即为 $w_i$
            update_amount = self.alpha * td_error * feature_value
            self.weights[feature_name] += update_amount
        
        return

    def final(self, state):
        "Called at the end of each game."
        # call the super-class final method
        PacmanQAgent.final(self, state)

        # did we finish training?
        if self.episodesSoFar == self.numTraining:
            # you might want to print your weights here for debugging
            pass