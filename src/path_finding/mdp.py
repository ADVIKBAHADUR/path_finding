"""
Markov Decision Process (MDP) Algorithms

MDPs are used for decision-making in stochastic environments where outcomes
are partly random and partly under the control of a decision maker.
This module includes Value Iteration and Policy Iteration algorithms.
"""

from typing import Dict, List, Tuple, Any, Optional, Callable
import numpy as np


class MDP:
    """
    Markov Decision Process class.
    
    Attributes:
        states: List of possible states
        actions: List of possible actions
        transition_prob: Function returning P(s'|s,a)
        reward: Function returning R(s,a,s')
        gamma: Discount factor (0 <= gamma < 1)
    """
    
    def __init__(
        self,
        states: List[Any],
        actions: List[Any],
        transition_prob: Callable[[Any, Any, Any], float],
        reward: Callable[[Any, Any, Any], float],
        gamma: float = 0.9
    ):
        """
        Initialize MDP.
        
        Args:
            states: List of all possible states
            actions: List of all possible actions
            transition_prob: Function(state, action, next_state) -> probability
            reward: Function(state, action, next_state) -> reward
            gamma: Discount factor for future rewards
        """
        self.states = states
        self.actions = actions
        self.transition_prob = transition_prob
        self.reward = reward
        self.gamma = gamma
    
    def value_iteration(self, epsilon: float = 0.01, max_iterations: int = 1000) -> Dict[Any, float]:
        """
        Perform value iteration to find optimal state values.
        
        Args:
            epsilon: Convergence threshold
            max_iterations: Maximum number of iterations
        
        Returns:
            Dictionary mapping states to their optimal values
        """
        V = {s: 0.0 for s in self.states}
        
        for _ in range(max_iterations):
            V_new = {}
            delta = 0.0
            
            for s in self.states:
                max_value = float('-inf')
                
                for a in self.actions:
                    value = 0.0
                    for s_next in self.states:
                        prob = self.transition_prob(s, a, s_next)
                        rew = self.reward(s, a, s_next)
                        value += prob * (rew + self.gamma * V[s_next])
                    
                    max_value = max(max_value, value)
                
                V_new[s] = max_value
                delta = max(delta, abs(V_new[s] - V[s]))
            
            V = V_new
            
            if delta < epsilon:
                break
        
        return V
    
    def extract_policy(self, V: Dict[Any, float]) -> Dict[Any, Any]:
        """
        Extract optimal policy from value function.
        
        Args:
            V: Value function (state -> value mapping)
        
        Returns:
            Policy (state -> action mapping)
        """
        policy = {}
        
        for s in self.states:
            best_action = None
            best_value = float('-inf')
            
            for a in self.actions:
                value = 0.0
                for s_next in self.states:
                    prob = self.transition_prob(s, a, s_next)
                    rew = self.reward(s, a, s_next)
                    value += prob * (rew + self.gamma * V[s_next])
                
                if value > best_value:
                    best_value = value
                    best_action = a
            
            policy[s] = best_action
        
        return policy
    
    def policy_iteration(self, max_iterations: int = 100) -> Tuple[Dict[Any, Any], Dict[Any, float]]:
        """
        Perform policy iteration to find optimal policy.
        
        Args:
            max_iterations: Maximum number of iterations
        
        Returns:
            Tuple of (optimal_policy, value_function)
        """
        # Initialize with random policy
        policy = {s: self.actions[0] for s in self.states}
        
        for _ in range(max_iterations):
            # Policy evaluation
            V = self._policy_evaluation(policy)
            
            # Policy improvement
            policy_stable = True
            new_policy = {}
            
            for s in self.states:
                old_action = policy[s]
                best_action = None
                best_value = float('-inf')
                
                for a in self.actions:
                    value = 0.0
                    for s_next in self.states:
                        prob = self.transition_prob(s, a, s_next)
                        rew = self.reward(s, a, s_next)
                        value += prob * (rew + self.gamma * V[s_next])
                    
                    if value > best_value:
                        best_value = value
                        best_action = a
                
                new_policy[s] = best_action
                
                if old_action != best_action:
                    policy_stable = False
            
            policy = new_policy
            
            if policy_stable:
                break
        
        V = self._policy_evaluation(policy)
        return policy, V
    
    def _policy_evaluation(
        self,
        policy: Dict[Any, Any],
        epsilon: float = 0.01,
        max_iterations: int = 1000
    ) -> Dict[Any, float]:
        """
        Evaluate a given policy.
        
        Args:
            policy: Policy to evaluate (state -> action mapping)
            epsilon: Convergence threshold
            max_iterations: Maximum number of iterations
        
        Returns:
            Value function for the given policy
        """
        V = {s: 0.0 for s in self.states}
        
        for _ in range(max_iterations):
            delta = 0.0
            V_new = {}
            
            for s in self.states:
                a = policy[s]
                value = 0.0
                
                for s_next in self.states:
                    prob = self.transition_prob(s, a, s_next)
                    rew = self.reward(s, a, s_next)
                    value += prob * (rew + self.gamma * V[s_next])
                
                V_new[s] = value
                delta = max(delta, abs(V_new[s] - V[s]))
            
            V = V_new
            
            if delta < epsilon:
                break
        
        return V


def solve_mdp_value_iteration(
    states: List[Any],
    actions: List[Any],
    transition_prob: Callable[[Any, Any, Any], float],
    reward: Callable[[Any, Any, Any], float],
    gamma: float = 0.9,
    epsilon: float = 0.01
) -> Tuple[Dict[Any, float], Dict[Any, Any]]:
    """
    Solve an MDP using value iteration.
    
    Args:
        states: List of all possible states
        actions: List of all possible actions
        transition_prob: Function(state, action, next_state) -> probability
        reward: Function(state, action, next_state) -> reward
        gamma: Discount factor
        epsilon: Convergence threshold
    
    Returns:
        Tuple of (value_function, optimal_policy)
    """
    mdp = MDP(states, actions, transition_prob, reward, gamma)
    V = mdp.value_iteration(epsilon)
    policy = mdp.extract_policy(V)
    return V, policy


def solve_mdp_policy_iteration(
    states: List[Any],
    actions: List[Any],
    transition_prob: Callable[[Any, Any, Any], float],
    reward: Callable[[Any, Any, Any], float],
    gamma: float = 0.9
) -> Tuple[Dict[Any, Any], Dict[Any, float]]:
    """
    Solve an MDP using policy iteration.
    
    Args:
        states: List of all possible states
        actions: List of all possible actions
        transition_prob: Function(state, action, next_state) -> probability
        reward: Function(state, action, next_state) -> reward
        gamma: Discount factor
    
    Returns:
        Tuple of (optimal_policy, value_function)
    """
    mdp = MDP(states, actions, transition_prob, reward, gamma)
    return mdp.policy_iteration()
