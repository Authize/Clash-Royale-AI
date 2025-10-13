#!/usr/bin/env python3
"""
Professional Training Monitor
Tracks all AI learning data and provides comprehensive analysis
"""

import json
import os
import time
from datetime import datetime
from collections import defaultdict
import numpy as np

class ProfessionalTrainingMonitor:
    def __init__(self):
        self.data_dir = "professional_training_data"
        os.makedirs(self.data_dir, exist_ok=True)
        
        # Training metrics
        self.training_metrics = {
            "total_episodes": 0,
            "total_actions": 0,
            "total_reward": 0,
            "avg_reward": 0,
            "best_reward": 0,
            "win_rate": 0,
            "elixir_efficiency": 0,
            "defensive_success_rate": 0,
            "offensive_success_rate": 0,
            "learning_curve": [],
            "performance_grades": []
        }
        
        # Card knowledge tracking
        self.card_knowledge = {}
        
        # Strategy effectiveness
        self.strategy_effectiveness = {
            "early_game": {},
            "mid_game": {},
            "late_game": {},
            "overtime": {}
        }
        
        # Elixir management analysis
        self.elixir_analysis = {
            "optimal_levels": {},
            "waste_patterns": {},
            "efficiency_ratings": {}
        }
        
        # Counter-strategy tracking
        self.counter_strategies = {
            "vs_swarm": {},
            "vs_air": {},
            "vs_ground": {},
            "vs_building": {}
        }
        
        # Positioning analysis
        self.positioning_analysis = {
            "optimal_positions": {},
            "defensive_positions": {},
            "offensive_positions": {}
        }
        
        # Timing analysis
        self.timing_analysis = {
            "optimal_timings": {},
            "counter_timings": {},
            "combo_timings": {}
        }
    
    def update_training_data(self, episode, total_reward, actions_taken, agent_data=None):
        """Update comprehensive training data"""
        self.training_metrics["total_episodes"] += 1
        self.training_metrics["total_actions"] += actions_taken
        self.training_metrics["total_reward"] += total_reward
        
        # Update averages
        self.training_metrics["avg_reward"] = (
            self.training_metrics["total_reward"] / self.training_metrics["total_episodes"]
        )
        
        # Update best reward
        if total_reward > self.training_metrics["best_reward"]:
            self.training_metrics["best_reward"] = total_reward
        
        # Update learning curve
        self.training_metrics["learning_curve"].append({
            "episode": episode,
            "reward": total_reward,
            "actions": actions_taken,
            "timestamp": datetime.now().isoformat()
        })
        
        # Update performance grade
        grade = self._calculate_performance_grade(total_reward)
        self.training_metrics["performance_grades"].append(grade)
        
        # Update agent-specific data if available
        if agent_data:
            self._update_agent_data(agent_data)
        
        # Save data
        self._save_training_data()
    
    def _calculate_performance_grade(self, reward):
        """Calculate performance grade based on reward"""
        if reward >= 100:
            return "A+"
        elif reward >= 80:
            return "A"
        elif reward >= 60:
            return "B"
        elif reward >= 40:
            return "C"
        elif reward >= 20:
            return "D"
        else:
            return "F"
    
    def _update_agent_data(self, agent_data):
        """Update agent-specific learning data"""
        try:
            # Update card knowledge
            if hasattr(agent_data, 'card_memory'):
                for card, data in agent_data.card_memory.items():
                    if card not in self.card_knowledge:
                        self.card_knowledge[card] = {
                            "total_uses": 0,
                            "successes": 0,
                            "avg_reward": 0,
                            "success_rate": 0
                        }
                    
                    self.card_knowledge[card]["total_uses"] += data.get("total_uses", 0)
                    self.card_knowledge[card]["successes"] += data.get("successes", 0)
                    self.card_knowledge[card]["avg_reward"] = data.get("avg_reward", 0)
                    
                    if data.get("total_uses", 0) > 0:
                        self.card_knowledge[card]["success_rate"] = (
                            data.get("successes", 0) / data.get("total_uses", 1) * 100
                        )
            
            # Update strategy effectiveness
            if hasattr(agent_data, 'battle_phase_strategies'):
                for phase, strategies in agent_data.battle_phase_strategies.items():
                    if phase not in self.strategy_effectiveness:
                        self.strategy_effectiveness[phase] = {}
                    
                    for strategy, data in strategies.items():
                        if strategy not in self.strategy_effectiveness[phase]:
                            self.strategy_effectiveness[phase][strategy] = {
                                "uses": 0,
                                "successes": 0,
                                "success_rate": 0
                            }
                        
                        self.strategy_effectiveness[phase][strategy]["uses"] += data.get("uses", 0)
                        self.strategy_effectiveness[phase][strategy]["successes"] += data.get("successes", 0)
                        
                        if data.get("uses", 0) > 0:
                            self.strategy_effectiveness[phase][strategy]["success_rate"] = (
                                data.get("successes", 0) / data.get("uses", 1) * 100
                            )
            
            # Update elixir analysis
            if hasattr(agent_data, 'elixir_management'):
                for action, data in agent_data.elixir_management.items():
                    if action not in self.elixir_analysis["optimal_levels"]:
                        self.elixir_analysis["optimal_levels"][action] = []
                    
                    self.elixir_analysis["optimal_levels"][action].extend(data.get("elixir_levels", []))
            
            # Update counter strategies
            if hasattr(agent_data, 'counter_strategies'):
                for enemy_type, strategies in agent_data.counter_strategies.items():
                    if enemy_type not in self.counter_strategies:
                        self.counter_strategies[enemy_type] = {}
                    
                    for strategy in strategies:
                        if strategy not in self.counter_strategies[enemy_type]:
                            self.counter_strategies[enemy_type][strategy] = 0
                        self.counter_strategies[enemy_type][strategy] += 1
            
            # Update positioning analysis
            if hasattr(agent_data, 'positioning_data'):
                for position, actions in agent_data.positioning_data.items():
                    if position not in self.positioning_analysis["optimal_positions"]:
                        self.positioning_analysis["optimal_positions"][position] = []
                    
                    self.positioning_analysis["optimal_positions"][position].extend(actions)
            
            # Update timing analysis
            if hasattr(agent_data, 'timing_patterns'):
                for action, data in agent_data.timing_patterns.items():
                    if action not in self.timing_analysis["optimal_timings"]:
                        self.timing_analysis["optimal_timings"][action] = {
                            "timings": [],
                            "success_rate": 0
                        }
                    
                    self.timing_analysis["optimal_timings"][action]["timings"].extend(data.get("timings", []))
                    self.timing_analysis["optimal_timings"][action]["success_rate"] = data.get("success_rate", 0)
        
        except Exception as e:
            print(f"Error updating agent data: {e}")
    
    def _convert_numpy_types(self, obj):
        """Convert NumPy types to native Python types for JSON serialization"""
        if isinstance(obj, np.integer):
            return int(obj)
        elif isinstance(obj, np.floating):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        elif isinstance(obj, dict):
            return {key: self._convert_numpy_types(value) for key, value in obj.items()}
        elif isinstance(obj, list):
            return [self._convert_numpy_types(item) for item in obj]
        else:
            return obj

    def _save_training_data(self):
        """Save comprehensive training data"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Save main training data
        training_data = {
            "timestamp": timestamp,
            "training_metrics": self.training_metrics,
            "card_knowledge": self.card_knowledge,
            "strategy_effectiveness": self.strategy_effectiveness,
            "elixir_analysis": self.elixir_analysis,
            "counter_strategies": self.counter_strategies,
            "positioning_analysis": self.positioning_analysis,
            "timing_analysis": self.timing_analysis
        }
        
        # Convert NumPy types to native Python types
        training_data = self._convert_numpy_types(training_data)
        
        filename = f"{self.data_dir}/professional_training_{timestamp}.json"
        with open(filename, 'w') as f:
            json.dump(training_data, f, indent=2)
        
        # Also save latest data
        latest_filename = f"{self.data_dir}/latest_training_data.json"
        with open(latest_filename, 'w') as f:
            json.dump(training_data, f, indent=2)
    
    def generate_professional_report(self):
        """Generate comprehensive professional training report"""
        report = {
            "timestamp": datetime.now().isoformat(),
            "training_summary": {
                "total_episodes": self.training_metrics["total_episodes"],
                "avg_reward": self.training_metrics["avg_reward"],
                "best_reward": self.training_metrics["best_reward"],
                "current_grade": self.training_metrics["performance_grades"][-1] if self.training_metrics["performance_grades"] else "N/A"
            },
            "card_performance": self._analyze_card_performance(),
            "strategy_analysis": self._analyze_strategies(),
            "elixir_efficiency": self._analyze_elixir_efficiency(),
            "counter_strategy_effectiveness": self._analyze_counter_strategies(),
            "positioning_effectiveness": self._analyze_positioning(),
            "timing_effectiveness": self._analyze_timing(),
            "recommendations": self._generate_recommendations()
        }
        
        # Convert NumPy types to native Python types
        report = self._convert_numpy_types(report)
        
        # Save report
        report_filename = f"{self.data_dir}/professional_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_filename, 'w') as f:
            json.dump(report, f, indent=2)
        
        return report
    
    def _analyze_card_performance(self):
        """Analyze card performance"""
        if not self.card_knowledge:
            return "No card data available"
        
        # Find best and worst performing cards
        best_cards = sorted(
            self.card_knowledge.items(),
            key=lambda x: x[1]["success_rate"],
            reverse=True
        )[:5]
        
        worst_cards = sorted(
            self.card_knowledge.items(),
            key=lambda x: x[1]["success_rate"]
        )[:5]
        
        return {
            "best_cards": best_cards,
            "worst_cards": worst_cards,
            "total_cards_learned": len(self.card_knowledge)
        }
    
    def _analyze_strategies(self):
        """Analyze strategy effectiveness"""
        strategy_analysis = {}
        
        for phase, strategies in self.strategy_effectiveness.items():
            if strategies:
                best_strategy = max(strategies.items(), key=lambda x: x[1]["success_rate"])
                strategy_analysis[phase] = {
                    "best_strategy": best_strategy,
                    "total_strategies": len(strategies)
                }
        
        return strategy_analysis
    
    def _analyze_elixir_efficiency(self):
        """Analyze elixir efficiency"""
        if not self.elixir_analysis["optimal_levels"]:
            return "No elixir data available"
        
        efficiency_analysis = {}
        for action, levels in self.elixir_analysis["optimal_levels"].items():
            if levels:
                efficiency_analysis[action] = {
                    "avg_elixir_level": np.mean(levels),
                    "optimal_range": [min(levels), max(levels)],
                    "usage_count": len(levels)
                }
        
        return efficiency_analysis
    
    def _analyze_counter_strategies(self):
        """Analyze counter strategy effectiveness"""
        counter_analysis = {}
        
        for enemy_type, strategies in self.counter_strategies.items():
            if strategies:
                most_used = max(strategies.items(), key=lambda x: x[1])
                counter_analysis[enemy_type] = {
                    "most_effective": most_used,
                    "total_counters": len(strategies)
                }
        
        return counter_analysis
    
    def _analyze_positioning(self):
        """Analyze positioning effectiveness"""
        if not self.positioning_analysis["optimal_positions"]:
            return "No positioning data available"
        
        positioning_analysis = {}
        for position, actions in self.positioning_analysis["optimal_positions"].items():
            if actions:
                positioning_analysis[position] = {
                    "most_common_action": max(set(actions), key=actions.count),
                    "total_actions": len(actions)
                }
        
        return positioning_analysis
    
    def _analyze_timing(self):
        """Analyze timing effectiveness"""
        if not self.timing_analysis["optimal_timings"]:
            return "No timing data available"
        
        timing_analysis = {}
        for action, data in self.timing_analysis["optimal_timings"].items():
            if data["timings"]:
                timing_analysis[action] = {
                    "avg_timing": np.mean(data["timings"]),
                    "success_rate": data["success_rate"],
                    "total_timings": len(data["timings"])
                }
        
        return timing_analysis
    
    def _generate_recommendations(self):
        """Generate training recommendations"""
        recommendations = []
        
        # Analyze performance trends
        if len(self.training_metrics["learning_curve"]) > 10:
            recent_rewards = [ep["reward"] for ep in self.training_metrics["learning_curve"][-10:]]
            if np.mean(recent_rewards) > self.training_metrics["avg_reward"]:
                recommendations.append("✅ Performance is improving! Continue current training approach.")
            else:
                recommendations.append("⚠️ Performance plateau detected. Consider adjusting learning rate or exploration.")
        
        # Analyze card usage
        if self.card_knowledge:
            underused_cards = [card for card, data in self.card_knowledge.items() if data["total_uses"] < 5]
            if underused_cards:
                recommendations.append(f"📚 Consider using these cards more: {underused_cards[:3]}")
        
        # Analyze strategy effectiveness
        if self.strategy_effectiveness:
            for phase, strategies in self.strategy_effectiveness.items():
                if strategies:
                    best_strategy = max(strategies.items(), key=lambda x: x[1]["success_rate"])
                    recommendations.append(f"🎯 Best {phase} strategy: {best_strategy[0]} ({best_strategy[1]['success_rate']:.1f}% success)")
        
        return recommendations

# Global instance
professional_monitor = ProfessionalTrainingMonitor()

