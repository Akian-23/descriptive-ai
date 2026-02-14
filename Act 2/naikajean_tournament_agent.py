#!/usr/bin/env python
"""
Tournament Agent: Stellar
Student:  Naika Jean
Generated: 2026-02-14 02:25:37

Evolution Details:
- Generations: 200
- Final Fitness: N/A
- Trained against: Grim Trigger, Tit-for-Two-Tats, Always Undercut, Generous Tit-for-Tat, Random (0.7)...

Strategy: Cooperates with cooperative opponents but retaliates against defectors
"""

from agents import Agent, INVEST, UNDERCUT
import random


class NaikaJeanAgent(Agent):
    """
    Stellar
    
    Cooperates with cooperative opponents but retaliates against defectors
    
    Evolved Genes: [1.0, 1.0, 0.2658705918345952, 0.0, 0.3634325947877103, 0.8891204962547128]
    """
    
    def __init__(self):
        # These genes were evolved through 200 generations
        self.genes = [1.0, 1.0, 0.2658705918345952, 0.0, 0.3634325947877103, 0.8891204962547128]
        
        # Required for tournament compatibility
        self.student_name = " Naika Jean"
        
        super().__init__(
            name="Stellar",
            description="Cooperates with cooperative opponents but retaliates against defectors"
        )
    
    def choose_action(self) -> bool:
        """
        IMPROVED decision logic - AGGRESSIVE VERSION
        More likely to retaliate, less exploitable
        """
        
        # First 3 rounds: use initial cooperation gene
        if self.round_num < 3:
            return random.random() < self.genes[0]
        
        # Calculate memory window
        memory_length = max(1, int(self.genes[4] * 10) + 1)
        recent_history = self.history[-memory_length:]
        cooperation_rate = sum(recent_history) / len(recent_history)
        
        # AGGRESSIVE STRATEGY: Higher threshold for cooperation
        
        # Only cooperate if opponent is VERY cooperative (>80%)
        if cooperation_rate > 0.8:
            return random.random() < self.genes[1]  # gene[1] should evolve HIGH
        
        # If somewhat cooperative (50-80%), be cautious
        elif cooperation_rate > 0.5:
            # Mix of cooperation and defection
            coop_prob = self.genes[1] * (cooperation_rate - 0.5) * 2  # Scale 0-1
            return random.random() < coop_prob
        
        # If aggressive (<50%), retaliate hard
        else:
            # Mostly defect, with small chance to forgive
            if random.random() < self.genes[3] * 0.3:  # Reduced forgiveness
                return INVEST
            else:
                return UNDERCUT



# Convenience function for tournament loading
def get_agent():
    """Return an instance of this agent for tournament use"""
    return NaikaJeanAgent()


if __name__ == "__main__":
    # Test that the agent can be instantiated
    agent = get_agent()
    print(f" Agent loaded successfully: {agent.name}")
    print(f"   Genes: {agent.genes}")
    print(f"   Description: {agent.description}")
