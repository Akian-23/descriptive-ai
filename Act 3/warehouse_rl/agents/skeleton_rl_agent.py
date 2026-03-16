#!/usr/bin/env python3
"""
Skeleton Optimization Agent - Template for students to implement optimization algorithms

IMPORTANT: This is NOT an RL agent - it's a template for 
students to implement their own optimization algorithms (greedy, Hungarian, etc.)

This agent currently makes terrible decisions:
- Random staffing decisions
- No layout optimization 
- Ignores order priorities
- No intelligent assignment logic

Students should replace the naive methods with proper optimization algorithms.
"""

from matplotlib.pyplot import grid
import numpy as np
from typing import Dict, Optional
from .standardized_agents import BaselineAgent

class SkeletonOptimizationAgent(BaselineAgent):
    """
    Template for students to implement their own optimization algorithms.
    
    Students should replace the naive methods with:
    - Economic models for staffing decisions
    - Hungarian algorithm for order assignment  
    - Greedy search for layout optimization
    - Multi-objective optimization techniques
    """
    
    def __init__(self, env):
        super().__init__(env)
        self.name = "StudentOptimization"
        
        # Enable unlimited hiring for true economic optimization
        self.env._unlimited_hiring = True
        
        # Students can add their own state tracking here
        self.performance_metrics = []
        self.decision_history = []
        
        # Students can add algorithm parameters here
        # Example: Hungarian algorithm matrices, greedy search parameters, etc.
        self.staffing_parameters = {
            'hire_threshold_ratio': 3.0,
            'fire_threshold_ratio': 2.0,
            'profit_threshold': 0
        }
        
        # Students can implement adaptive parameters that change based on performance
        self.adaptive_optimization_enabled = False
        
    def reset(self):
        """Reset agent state - students should expand this"""
        self.action_history = []
        self.reward_history = []
        # TODO: Reset any neural network states, replay buffers, etc.
    
   
    def _get_naive_staffing_action(self, financial_state, employee_info) -> int:
        """
        WEEK 2 STEP 1: Economic staffing optimization
        Make hiring/firing decisions based on simple business economics
        """
        # Extract economic and operational data
        current_profit = financial_state[0]
        revenue = financial_state[1]
        costs = financial_state[2]
        burn_rate = financial_state[3]
        
        num_employees = len(self.env.employees)
        queue_length = len(self.env.order_queue.orders)
        has_manager = np.any(employee_info[:, 5] == 1)
        idle_workers = len([e for e in employee_info if e[2] == 0 and e[5] == 0])

        if num_employees == 0:
            return 1  # Always hire first worker
                
        # Business indicators
        queue_pressure = queue_length / max(1, num_employees)
        layout_efficiency = getattr(self.env, "layout_efficiency", 0.5)  # default to 0.5 if not set
        profit_per_employee = current_profit / max(1, num_employees
        
        # Economic parameters
        hire_threshold = 2.5    # buffer zone: hire if queue_pressure > 2.5
        fire_threshold = 2.0     # fire if queue_pressure < 2.0
        manager_threshold = 2000 # only hire manager if profit > $2000
        min_staff = 2            # never fire below 2 employees
        max_staff = 20
        fire_cooldown = 20  # timesteps before firing again
        
        # Track last firing timestep
            if not hasattr(self, "_last_firing"):
                self._last_firing = -fire_cooldown


        # Hire worker if queue pressure high and below max staff
        if queue_pressure > hire_threshold and num_employees < max_staff:
            return 1  # hire worker
        
        # Hire manager if none exists and profit allows
        if not has_manager and current_profit > manager_threshold:
            return 3  # hire manager

        # Fire worker if queue low and many idle workers, but stay above min staff
        # if queue_pressure < fire_threshold and num_employees > min_staff:
        #    return 2  # fire worker


        # ---- FIRING LOGIC ----
        can_fire = (
            queue_pressure < fire_threshold
            and num_employees > min_staff
            and idle_workers >= 1
            and profit_per_employee > 20  # avoid firing if revenue too low
            and layout_efficiency > 0.5   # only fire if layout is decent
            and (timestep - self._last_firing) >= fire_cooldown  # cooldown
        )

        if can_fire:
            self._last_firing = timestep
            return 2  # fire worker

        return 0

    def _get_naive_layout_action(self, current_timestep) -> list:
        """
        WEEK 1 STEP 1: Layout optimization - students should improve this!
        
        Current problems:
        - Random swaps with no strategic purpose
        - Ignores item co-occurrence patterns
        - No consideration of delivery distances
        - Wastes manager time on pointless moves
        """
        # TODO WEEK 1 STEP 1: Students should implement intelligent layout optimization
        # Current approach: Occasionally make random swaps

        # Only optimize every 100 timesteps
        if current_timestep % 100 != 0:
            return [0, 0]

        grid = self.env.warehouse_grid

        # Step 1: Get item frequency data
        if not hasattr(grid, "item_access_frequency"):
            return [0, 0]

        frequencies = np.array(grid.item_access_frequency)
        active_items = np.where(frequencies > 0)[0]
        if len(active_items) == 0:
            return [0, 0]

        # Step 2: Identify hot items (top 25%)
        threshold = np.percentile(frequencies[active_items], 75)
        hot_items = active_items[frequencies[active_items] >= threshold]

        # Step 3: Get delivery positions
        delivery_positions = getattr(grid, "truck_bay_positions", [(grid.width // 2, grid.height // 2)])

        best_swap = None
        best_benefit = 0

        # Step 4: Evaluate each hot item
        for item in hot_items:
            locations = grid.find_item_locations(item)
            if not locations:
                continue
            current_pos = locations[0]
            
            current_distance = min(
                grid.manhattan_distance(current_pos, d)
                for d in delivery_positions
            )

            # Only optimize if far from delivery
            if current_distance <= 3:
                continue

            # Use helper to find best swap
            swap = self._find_closer_position(current_pos, delivery_positions)
            if swap:
                current_index, target_index = swap
                # Convert back to 2D for distance calculation
                current_pos_2d = (current_index // grid.width, current_index % grid.width)
                target_pos_2d = (target_index // grid.width, target_index % grid.width)
                distance_saved = min(
                    grid.manhattan_distance(current_pos_2d, d) for d in delivery_positions
                ) - min(grid.manhattan_distance(target_pos_2d, d) for d in delivery_positions)
                benefit = distance_saved * frequencies[item]
                if benefit > best_benefit:
                    best_benefit = benefit
                    best_swap = swap

        # Step 6: Return the swap if beneficial
        if best_swap:
            print(f"Timestep {current_timestep}: hot_items={hot_items}")
            print(f"Best swap found: {best_swap}, benefit={best_benefit}")
            print(f"Delivery positions: {delivery_positions}")
            self.action_history.append({'layout_swap': best_swap, 'layout_phase': 1})
            return best_swap
        
        # Phase 2: Co-occurrence clustering (optional, every 200 steps)
        if current_timestep % 200 == 0:
            cooccurrence_swap = self._find_cooccurrence_swap()
            if cooccurrence_swap:
                self.action_history.append({'layout_swap': cooccurrence_swap, 'layout_phase': 2})
                print(f"Phase 2 swap: {cooccurrence_swap}")
                return cooccurrence_swap

        
        # No swap
        print(f"Timestep {current_timestep}: hot_items={hot_items}")
        print("No beneficial swap found")
        print(f"Delivery positions: {delivery_positions}")
        return [0, 0]  # No beneficial swap found
    


    # Helper method for Step 5
    def _find_closer_position(self, current_pos, delivery_positions, min_improvement=1):
        """
        Greedy neighborhood search for better item placement.

        Searches all storage positions to find the one that gives the largest
        distance improvement toward delivery points.

        Returns [current_index, target_index] if beneficial swap found.
        """
        grid = self.env.warehouse_grid
        best_swap = None
        current_idx = current_pos[1] * grid.width + current_pos[0]

        current_dist = min(grid.manhattan_distance(current_pos, d) for d in delivery_positions)
        best_improvement = 0

        for y in range(grid.height):
            for x in range(grid.width):
                if grid.cell_types[y, x] != 1:  # Only storage
                    continue

                # Skip if already occupied by the same item
                if (x, y) == current_pos:
                    continue

                new_dist = min(grid.manhattan_distance((x, y), d) for d in delivery_positions)
                improvement = current_dist - new_dist
                if improvement > best_improvement and improvement >= min_improvement:
                    best_improvement = improvement
                    target_idx = y * grid.width + x
                    best_swap = [current_idx, target_idx]
                    
        # Debug info
        if best_swap:
            print(f"Found better position: {best_swap}, improvement={best_improvement}")
        return best_swap    
    
    # Helper method for Phase 2: co-occurrence clustering
    def _find_cooccurrence_swap(self):
        """
        Greedy clustering algorithm for association-based spatial optimization.
        
        Returns swap that maximizes benefit = co-occurrence_frequency × distance_saved
        """
        grid = self.env.warehouse_grid
        cooccurrence = grid.item_cooccurrence
        
        # Parameters
        min_cooccurrence = 2
        min_distance = 3
        best_benefit = 0
        best_swap = None
        
        num_items = cooccurrence.shape[0]
        
        for item1 in range(num_items):
            for item2 in range(item1 + 1, num_items):
                frequency = cooccurrence[item1, item2]
                if frequency <= min_cooccurrence:
                    continue
                
                loc1 = grid.find_item_locations(item1)
                loc2 = grid.find_item_locations(item2)
                
                if not loc1 or not loc2:
                    continue
                
                r1, c1 = loc1[0]
                r2, c2 = loc2[0]
                
                current_distance = abs(r1 - r2) + abs(c1 - c2)
                if current_distance <= min_distance:
                    continue
                
                benefit = frequency * current_distance
                if benefit > best_benefit:
                    best_benefit = benefit
                    
                    # Try adjacent empty spot near item1
                    neighbors = [(r1, c1 + 1), (r1, c1 - 1), (r1 + 1, c1), (r1 - 1, c1)]
                    found = False
                    for nr, nc in neighbors:
                        if 0 <= nr < grid.height and 0 <= nc < grid.width:
                            if grid.cell_types[nr, nc] == 1:
                                best_swap = [r2 * grid.width + c2, nr * grid.width + nc]
                                found = True
                                break
                    if not found:
                        best_swap = [r2 * grid.width + c2, r1 * grid.width + c1]
        
        return best_swap
    
    def track_layout_performance(self):
        """
        Performance analysis for greedy layout optimization algorithms.
        
        Measures: 
        - Layout efficiency (frequency-weighted distances)
        - Algorithm convergence (swaps per period)
        - Optimization impact over time
        """
        if not hasattr(self, 'layout_metrics'):
            self.layout_metrics = []
        
        # Calculate current layout efficiency using weighted distance metric
        efficiency = self._calculate_layout_efficiency()
        
        self.layout_metrics.append({
            'timestep': self.env.current_timestep,
            'efficiency': efficiency,
            'total_swaps': len([a for a in self.action_history if a['layout_swap'] != [0, 0]]),
            'phase1_swaps': self._count_frequency_swaps(),
            'phase2_swaps': self._count_cooccurrence_swaps()
        })
        
        # Print progress every 1000 steps
        if self.env.current_timestep % 1000 == 0:
            recent_efficiency = np.mean([m['efficiency'] for m in self.layout_metrics[-10:]])
            print(f"Layout efficiency: {recent_efficiency:.3f}")

    def _calculate_layout_efficiency(self):
        """
        Calculate a frequency-weighted layout efficiency score.
        
        Efficiency = 1 - (weighted_avg_distance / max_possible_distance)
        """
        grid = self.env.warehouse_grid

        if not hasattr(grid, "item_access_frequency"):
            return 0.5  # fallback

        frequencies = np.array(grid.item_access_frequency)
        active_items = np.where(frequencies > 0)[0]
        if len(active_items) == 0:
            return 0.0  # fallback

        delivery_positions = getattr(grid, "truck_bay_positions", [(grid.width // 2, grid.height // 2)])

        weighted_distance_sum = 0
        total_frequency = 0

        for item in active_items:
            locations = grid.find_item_locations(item)
            if not locations:
                continue
            pos = locations[0]
            min_dist = min(grid.manhattan_distance(pos, d) for d in delivery_positions)
            weighted_distance_sum += min_dist * frequencies[item]
            total_frequency += frequencies[item]

        if total_frequency == 0:
            return 0.5

        avg_weighted_distance = weighted_distance_sum / total_frequency
        max_possible_distance = grid.width + grid.height  # worst-case distance
        efficiency = 1.0 - (avg_weighted_distance / max_possible_distance)
        return efficiency

    # Optional helpers to count swaps per phase
    def _count_frequency_swaps(self):
        """Count how many swaps came from Phase 1 (frequency-based)"""
        if not hasattr(self, 'action_history'):
            return 0
        return sum(1 for a in self.action_history if a.get('layout_phase') == 1)


    def _count_cooccurrence_swaps(self):
        """Count how many swaps came from Phase 2 (co-occurrence clustering)"""
        if not hasattr(self, 'action_history'):
            return 0
        return sum(1 for a in self.action_history if a.get('layout_phase') == 2)
    

    def _get_naive_order_assignments(self, queue_info, employee_info) -> list:
        """
        WEEK 2 STEP 2: Worker-to-order matching optimization
        Greedy algorithm that assigns the best worker to each order based on
        distance and order value.
        """

        # Initialize assignments list (max 20 orders in action space)
        assignments = [0] * 20

        # Identify idle workers
        idle_workers = self._get_idle_workers(employee_info)

        # Get pending orders (limit to 20)
        pending_orders = self.env.order_queue.orders[:20]

        # If no workers or no orders, return empty assignments
        if not idle_workers or not pending_orders:
            return assignments

        # Number of orders waiting
        queue_len = len(pending_orders)

        # Store all worker–order pair scores
        scores = []

        # Used to normalize order values
        max_order_value = max(o.value for o in pending_orders)

        # Evaluate every worker–order pair
        for w_idx, w_pos in idle_workers:
            for o_idx, order in enumerate(pending_orders):

                # Calculate distance from worker to closest item in order
                try:
                    dist = self._calculate_order_distance(w_pos, order)
                except AttributeError:
                    dist = 100  # fallback if item location fails

                # Normalize distance score (closer = better)
                max_dist = self.env.warehouse_grid.width + self.env.warehouse_grid.height
                dist_score = 1 - (dist / max_dist)

                # Normalize order value (higher value = better)
                val_score = order.value / max_order_value

                # If queue is long, prioritize distance more heavily
                if queue_len > 10:
                    weight_dist = 0.85
                else:
                    weight_dist = 0.75

                weight_val = 1 - weight_dist

                # Combined optimization score
                combined_score = weight_dist * dist_score + weight_val * val_score

                # Store score with worker index and order index
                scores.append((combined_score, w_idx, o_idx))

        # Sort matches from best score to worst
        scores.sort(reverse=True)

        # Track which workers and orders are already assigned
        assigned_workers = set()
        assigned_orders = set()

        # Greedy assignment: pick highest score pairs first
        for score, w_idx, o_idx in scores:

            # Stop if all workers are already assigned
            if len(assigned_workers) >= len(idle_workers):
                break

            # Assign worker if both worker and order are still free
            if w_idx not in assigned_workers and o_idx not in assigned_orders:
                assignments[o_idx] = w_idx + 1  # +1 because environment uses 1-indexing
                assigned_workers.add(w_idx)
                assigned_orders.add(o_idx)

        return assignments
    
    def _calculate_order_distance(self, worker_pos, order):
        """
        Calculate minimum distance from worker to any item needed for this order.
        
        Algorithm: Find closest item location for each item type in order,
        return minimum distance across all required items.
        """
        min_distance = float('inf')
        grid = self.env.warehouse_grid     

        # TODO: For each item type in order.items:
        # TODO: - Find item locations using grid.find_item_locations()
        # TODO: - Calculate distance from worker_pos to each location
        # TODO: - Track minimum distance found

        for item_type in order.items:

            item_locations = grid.find_item_locations(item_type)

            for loc in item_locations:

                dist = abs(worker_pos[0] - loc[0]) + abs(worker_pos[1] - loc[1])

                if dist < min_distance:
                    min_distance = dist


        return min_distance if min_distance != float('inf') else 0

    def _get_idle_workers(self, employee_info):

        """
        Identify workers available for order assignment.
        
        Returns list of (worker_index, worker_position) for available workers.
        """
        idle_workers = []
        
        # TODO: Loop through employee_info array
        # TODO: Check if employee is active, idle, and not a manager
        # TODO: Extract position and add to idle_workers list
        # HINT: employee_info format: [x, y, state, has_order, items_collected, is_manager]
        
        for idx, e in enumerate(employee_info):

            x, y, state, has_order, items_collected, is_manager = e

            if state == 0 and has_order == 0 and is_manager == 0:

                idle_workers.append((idx, (int(x), int(y))))

        return idle_workers
    
    def get_action(self, observation: Dict) -> Dict:
        """
        Unified agent action:
        - Layout optimization (Week 1)
        - Staffing optimization (Week 2)
        - Order assignment optimization (Week 2)
        - Tracks integrated performance (Step 4)
        """
        current_timestep = observation['time'][0]
        financial_state = observation['financial']
        queue_info = observation['order_queue']
        employee_info = observation['employees']

        # Generate naive decisions
        layout_action = self._get_naive_layout_action(current_timestep) # week 1
        staffing_action = self._get_naive_staffing_action(financial_state, employee_info) # week 2
        order_assignments = self._get_naive_order_assignments(queue_info, employee_info)

        # Package action 
        action = {
            'layout_swap': layout_action,
            'staffing_action': staffing_action,
            'order_assignments': order_assignments
        }

        # Track integrated performance every 100 timesteps 
        if current_timestep % 100 == 0:
            self.track_integrated_performance()

        # Track layout-specific performance every 100 timesteps 
        if current_timestep % 100 == 0:
            self.track_layout_performance()

        # Record action 
        self.action_history.append(action.copy())

        return action
    
    def track_integrated_performance(self):
        """
        Performance analysis for integrated optimization system.
        
        Measures:
        - Economic efficiency (profit per employee)
        - Assignment quality (distance vs value optimization)
        - Layout effectiveness (from Week 1)
        - Overall system performance
        """
        if not hasattr(self, 'integrated_metrics'):
            self.integrated_metrics = []
        
        # Calculate comprehensive performance metrics
        current_profit = self.env.cumulative_profit
        num_employees = len(self.env.employees)
        queue_length = len(self.env.order_queue.orders)
        
        # TODO: Calculate economic efficiency metrics
        # TODO: Calculate assignment quality metrics  
        # TODO: Calculate layout efficiency (from Week 1)
        # TODO: Track optimization decisions made
        
        profit_per_employee = current_profit / max(1, num_employees)
        queue_pressure = queue_length / max(1, num_employees)
        total_decisions = len([a for a in getattr(self, 'action_history', []) if any(a.values())])
        layout_efficiency = self._calculate_layout_efficiency()  # From Week 1
            
        self.integrated_metrics.append({
            'timestep': self.env.current_timestep,
            'profit_per_employee': profit_per_employee,
            'queue_pressure': queue_pressure,
            'total_decisions': total_decisions,
            'layout_efficiency': layout_efficiency
        })
        
        # Print integrated progress every 1000 steps
        if self.env.current_timestep % 1000 == 0:
            recent_metrics = self.integrated_metrics[-10:]
            avg_profit_per_emp = np.mean([m['profit_per_employee'] for m in recent_metrics])
            avg_queue_pressure = np.mean([m['queue_pressure'] for m in recent_metrics])
            print(f"Integrated Performance: ${avg_profit_per_emp:.0f}/employee, Queue pressure: {avg_queue_pressure:.2f}")
        
    def analyze_optimization_contributions(self):
        """
        Analyze contribution of each optimization area to overall warehouse performance.
        Provides insight into which areas give highest ROI.
        """
        
        contributions = {
            "layout": 0.0,
            "staffing": 0.0,
            "assignment": 0.0
        }
        
        # Layout optimization: measure change in average pick distance
        if hasattr(self, "layout_metrics"):
            before = self.layout_metrics.get("avg_distance_before", 1)
            after = self.layout_metrics.get("avg_distance_after", 1)
            contributions["layout"] = max(0, (before - after) / before)
        
        # Staffing optimization: measure capacity utilization improvement
        if hasattr(self, "staffing_metrics"):
            utilization_before = self.staffing_metrics.get("utilization_before", 0.1)
            utilization_after = self.staffing_metrics.get("utilization_after", 0.1)
            contributions["staffing"] = max(0, (utilization_after - utilization_before) / utilization_before)
        
        # Assignment optimization: measure quality of assignments (distance + value)
        if hasattr(self, "assignment_metrics"):
            score_before = self.assignment_metrics.get("avg_score_before", 0.1)
            score_after = self.assignment_metrics.get("avg_score_after", 0.1)
            contributions["assignment"] = max(0, (score_after - score_before) / score_before)
        
        # Print or log contributions for Week 3 weighting decisions
        print("Optimization contributions (normalized):")
        for area, value in contributions.items():
            print(f"  {area.capitalize()}: {value:.2f}")
        
        return contributions
    
    def record_reward(self, reward: float):
        """
        WEEK 3 STEP 1: Reward tracking and learning - students should expand this
        
        TODO WEEK 3 STEP 1: Students should implement:
        - Proper reward tracking
        - Performance analysis
        - Adaptive parameter adjustment
        - Multi-objective optimization
        """
        self.reward_history.append(reward)
        
        # Skeleton optimization - doesn't actually learn anything useful
        if len(self.reward_history) > 10:
            # "Update" weights randomly (this doesn't actually improve performance)
            if reward > 0:
                self.staffing_weights += np.random.randn(4) * 0.01
                self.layout_weights += np.random.randn(3) * 0.01
    
    def should_update_policy(self) -> bool:
        """
        WEEK 3 STEP 2: Policy updates and adaptation - students should improve this
        
        TODO WEEK 3 STEP 2: Students should implement proper update schedules
        """
        return len(self.action_history) % 50 == 0  # Arbitrary update frequency
    
    def get_performance_metrics(self) -> Dict:
        """
        Get agent performance metrics for analysis
        Students can use this to debug their improvements
        """
        if not self.reward_history:
            return {"avg_reward": 0, "total_actions": 0}
        
        return {
            "avg_reward": np.mean(self.reward_history[-100:]),  # Last 100 rewards
            "total_actions": len(self.action_history),
            "exploration_rate": self.exploration_rate,
            "recent_performance": np.mean(self.reward_history[-10:]) if len(self.reward_history) >= 10 else 0
        }


def create_skeleton_optimization_agent(env) -> SkeletonOptimizationAgent:
    """Factory function to create skeleton Optimization agent"""
    return SkeletonOptimizationAgent(env)


# TODO: Students should implement these advanced components:

class StudentOptimizationAgent(SkeletonOptimizationAgent):
    """
    Template for students to implement their improved Optimization agent
    
    Suggested improvements:
    1. Replace random staffing with demand-based hiring
    2. Implement proper layout optimization using item frequencies
    3. Add distance-based order assignment
    4. Implement basic Q-optimization or policy gradients
    5. Add proper exploration vs exploitation balance
    """
    
    def __init__(self, env):
        super().__init__(env)
        self.name = "StudentOptimization"
        
        # TODO: Students implement these
        # self.q_table = {}
        # self.policy_network = SimpleNeuralNetwork()
        # self.experience_buffer = []
        # self.target_network = None
        
    def _get_improved_staffing_action(self, financial_state, employee_info, queue_info):
        """
        WEEK 2 STEP 1: Students implement intelligent staffing:
        - Hire when queue is growing
        - Fire when queue is empty for extended periods
        - Consider profit margins before hiring
        - Balance managers vs workers
        """
        pass
    
    def _get_improved_layout_action(self, observation):
        """
        WEEK 1 STEP 1: Students implement smart layout optimization:
        - Move frequently accessed items closer to delivery
        - Group items that are often ordered together
        - Only optimize when queue is manageable
        - Track swap effectiveness
        """
        pass
    
    def _get_improved_order_assignments(self, queue_info, employee_info):
        """
        WEEK 2 STEP 2: Students implement efficient order assignment:
        - Assign orders to closest available employees
        - Prioritize high-value or urgent orders
        - Consider employee current locations
        - Balance workload across employees
        """
        pass
    
    def learn_from_experience(self, state, action, reward, next_state, done):
        """
        WEEK 3 STEP 3: Students implement multi-objective optimization:
        - Performance trend analysis
        - Adaptive parameter tuning
        - Multi-objective trade-off handling
        - Robust optimization techniques
        """
        pass