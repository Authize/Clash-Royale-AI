#!/usr/bin/env python3
"""
Enhanced Learning System for CRAI
Advanced AI learning with improved game outcome analysis
"""

import os
import json
import time
import numpy as np
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass, asdict
from collections import defaultdict, deque
from datetime import datetime
import torch
import torch.nn as nn

@dataclass
class GameAnalysis:
    """Comprehensive game analysis for learning"""
    episode: int
    total_reward: float
    steps: int
    outcome: str  # victory, defeat, draw
    duration: float
    
    # Performance metrics
    elixir_efficiency: float
    damage_dealt: float
    damage_taken: float
    tower_damage: float
    enemy_tower_damage: float
    
    # Strategy analysis
    cards_played: List[str]
    successful_strategies: List[str]
    failed_strategies: List[str]
    enemy_patterns: List[str]
    
    # Learning insights
    key_moments: List[Dict]
    mistakes: List[Dict]
    improvements: List[Dict]
    
    # Context
    battle_phase: str
    enemy_deck_type: str
    difficulty_level: str

@dataclass
class LearningInsight:
    """Individual learning insight"""
    insight_type: str  # strategy, timing, positioning, counter
    description: str
    confidence: float
    evidence: List[str]
    action_recommendation: str
    priority: int  # 1-10, higher is more important

class EnhancedLearningSystem:
    """Advanced learning system with comprehensive game analysis"""
    
    def __init__(self, data_dir: str = "enhanced_learning_data"):
        self.data_dir = data_dir
        os.makedirs(data_dir, exist_ok=True)
        
        # Learning components
        self.game_analyses = deque(maxlen=1000)  # Keep last 1000 games
        self.learning_insights = []
        self.strategy_effectiveness = defaultdict(list)
        self.pattern_recognition = defaultdict(int)
        self.adaptation_rules = {}
        
        # Performance tracking
        self.performance_history = deque(maxlen=100)
        self.improvement_tracking = {
            "win_rate": [],
            "elixir_efficiency": [],
            "damage_ratio": [],
            "strategy_success": []
        }
        
        # Learning parameters
        self.learning_rate = 0.01
        self.adaptation_threshold = 0.7
        self.insight_confidence_threshold = 0.6
        
        # Analysis tools
        self.pattern_analyzer = PatternAnalyzer()
        self.strategy_analyzer = StrategyAnalyzer()
        self.mistake_analyzer = MistakeAnalyzer()
        self.improvement_analyzer = ImprovementAnalyzer()
    
    def analyze_game(self, game_data: Dict) -> GameAnalysis:
        """Comprehensive game analysis"""
        try:
            # Extract basic information
            analysis = GameAnalysis(
                episode=game_data.get('episode', 0),
                total_reward=game_data.get('total_reward', 0),
                steps=game_data.get('steps', 0),
                outcome=game_data.get('outcome', 'unknown'),
                duration=game_data.get('duration', 0),
                
        # Performance metrics
        elixir_efficiency=self._calculate_elixir_efficiency(game_data),
        damage_dealt=float(game_data.get('damage_dealt', 0)),
        damage_taken=float(game_data.get('damage_taken', 0)),
        tower_damage=float(game_data.get('tower_damage', 0)),
        enemy_tower_damage=float(game_data.get('enemy_tower_damage', 0)),
                
                # Strategy analysis
                cards_played=game_data.get('cards_played', []),
                successful_strategies=game_data.get('successful_strategies', []),
                failed_strategies=game_data.get('failed_strategies', []),
                enemy_patterns=game_data.get('enemy_patterns', []),
                
                # Learning insights
                key_moments=self._identify_key_moments(game_data),
                mistakes=self._identify_mistakes(game_data),
                improvements=self._identify_improvements(game_data),
                
                # Context
                battle_phase=game_data.get('battle_phase', 'unknown'),
                enemy_deck_type=game_data.get('enemy_deck_type', 'unknown'),
                difficulty_level=game_data.get('difficulty_level', 'medium')
            )
            
            # Store analysis
            self.game_analyses.append(analysis)
            
            # Generate learning insights
            insights = self._generate_learning_insights(analysis)
            self.learning_insights.extend(insights)
            
            # Update performance tracking
            self._update_performance_tracking(analysis)
            
            # Save analysis
            self._save_analysis(analysis)
            
            return analysis
            
        except Exception as e:
            print(f"❌ Error analyzing game: {e}")
            return None
    
    def _calculate_elixir_efficiency(self, game_data: Dict) -> float:
        """Calculate elixir efficiency score"""
        try:
            elixir_used = game_data.get('elixir_used', 0)
            damage_dealt = game_data.get('damage_dealt', 0)
            
            if elixir_used == 0:
                return 0.0
            
            # Efficiency = damage per elixir
            efficiency = damage_dealt / elixir_used
            
            # Normalize to 0-1 scale
            return min(1.0, efficiency / 10.0)
            
        except Exception:
            return 0.0
    
    def _identify_key_moments(self, game_data: Dict) -> List[Dict]:
        """Identify key moments in the game"""
        key_moments = []
        
        # High reward moments
        if game_data.get('max_reward', 0) > 50:
            key_moments.append({
                'type': 'high_reward',
                'description': 'High reward action taken',
                'reward': game_data.get('max_reward', 0),
                'timestamp': game_data.get('max_reward_time', 0)
            })
        
        # Tower damage moments
        if game_data.get('tower_damage', 0) > 100:
            key_moments.append({
                'type': 'tower_damage',
                'description': 'Significant tower damage dealt',
                'damage': game_data.get('tower_damage', 0)
            })
        
        # Elixir waste moments
        if game_data.get('elixir_waste', 0) > 5:
            key_moments.append({
                'type': 'elixir_waste',
                'description': 'Significant elixir waste detected',
                'waste': game_data.get('elixir_waste', 0)
            })
        
        return key_moments
    
    def _identify_mistakes(self, game_data: Dict) -> List[Dict]:
        """Identify mistakes made during the game"""
        mistakes = []
        
        # Low elixir efficiency
        if game_data.get('elixir_efficiency', 1.0) < 0.5:
            mistakes.append({
                'type': 'elixir_inefficiency',
                'description': 'Poor elixir management',
                'severity': 'high',
                'suggestion': 'Better elixir planning needed'
            })
        
        # Failed strategies
        for strategy in game_data.get('failed_strategies', []):
            mistakes.append({
                'type': 'failed_strategy',
                'description': f'Strategy failed: {strategy}',
                'severity': 'medium',
                'suggestion': f'Reconsider {strategy} strategy'
            })
        
        # High damage taken
        if game_data.get('damage_taken', 0) > 500:
            mistakes.append({
                'type': 'high_damage_taken',
                'description': 'Too much damage taken',
                'severity': 'high',
                'suggestion': 'Improve defensive positioning'
            })
        
        return mistakes
    
    def _identify_improvements(self, game_data: Dict) -> List[Dict]:
        """Identify potential improvements"""
        improvements = []
        
        # Successful strategies to reinforce
        for strategy in game_data.get('successful_strategies', []):
            improvements.append({
                'type': 'strategy_reinforcement',
                'description': f'Reinforce successful strategy: {strategy}',
                'priority': 'high',
                'action': f'Increase usage of {strategy}'
            })
        
        # Enemy patterns to counter
        for pattern in game_data.get('enemy_patterns', []):
            improvements.append({
                'type': 'counter_strategy',
                'description': f'Develop counter for: {pattern}',
                'priority': 'medium',
                'action': f'Learn to counter {pattern}'
            })
        
        return improvements
    
    def _generate_learning_insights(self, analysis: GameAnalysis) -> List[LearningInsight]:
        """Generate learning insights from game analysis"""
        insights = []
        
        # Strategy effectiveness insights
        for strategy in analysis.successful_strategies:
            insight = LearningInsight(
                insight_type='strategy',
                description=f'Strategy {strategy} was successful',
                confidence=0.8,
                evidence=[f'Used in {analysis.battle_phase} phase', 'Positive outcome'],
                action_recommendation=f'Increase usage of {strategy}',
                priority=7
            )
            insights.append(insight)
        
        # Mistake insights
        for mistake in analysis.mistakes:
            insight = LearningInsight(
                insight_type='mistake',
                description=mistake['description'],
                confidence=0.9,
                evidence=[f'Game outcome: {analysis.outcome}', f'Reward: {analysis.total_reward}'],
                action_recommendation=mistake['suggestion'],
                priority=8 if mistake['severity'] == 'high' else 5
            )
            insights.append(insight)
        
        # Pattern recognition insights
        for pattern in analysis.enemy_patterns:
            insight = LearningInsight(
                insight_type='pattern',
                description=f'Enemy pattern detected: {pattern}',
                confidence=0.7,
                evidence=[f'Deck type: {analysis.enemy_deck_type}', f'Phase: {analysis.battle_phase}'],
                action_recommendation=f'Develop counter for {pattern}',
                priority=6
            )
            insights.append(insight)
        
        return insights
    
    def _update_performance_tracking(self, analysis: GameAnalysis):
        """Update performance tracking metrics"""
        # Win rate
        win_rate = 1.0 if analysis.outcome == 'victory' else 0.0
        self.improvement_tracking['win_rate'].append(win_rate)
        
        # Elixir efficiency
        self.improvement_tracking['elixir_efficiency'].append(analysis.elixir_efficiency)
        
        # Damage ratio
        damage_ratio = analysis.damage_dealt / max(1, analysis.damage_taken)
        self.improvement_tracking['damage_ratio'].append(damage_ratio)
        
        # Strategy success rate
        strategy_success = len(analysis.successful_strategies) / max(1, len(analysis.successful_strategies) + len(analysis.failed_strategies))
        self.improvement_tracking['strategy_success'].append(strategy_success)
    
    def get_learning_recommendations(self) -> List[Dict]:
        """Get actionable learning recommendations"""
        recommendations = []
        
        # Analyze recent performance
        recent_analyses = list(self.game_analyses)[-10:]  # Last 10 games
        
        if not recent_analyses:
            return recommendations
        
        # Win rate analysis
        recent_wins = sum(1 for a in recent_analyses if a.outcome == 'victory')
        win_rate = recent_wins / len(recent_analyses)
        
        if win_rate < 0.3:
            recommendations.append({
                'type': 'urgent',
                'title': 'Low Win Rate',
                'description': f'Win rate is {win_rate:.1%}',
                'action': 'Focus on fundamental strategies',
                'priority': 10
            })
        
        # Elixir efficiency analysis
        avg_elixir_efficiency = np.mean([a.elixir_efficiency for a in recent_analyses])
        if avg_elixir_efficiency < 0.5:
            recommendations.append({
                'type': 'improvement',
                'title': 'Poor Elixir Management',
                'description': f'Elixir efficiency: {avg_elixir_efficiency:.2f}',
                'action': 'Improve elixir planning and timing',
                'priority': 8
            })
        
        # Strategy analysis
        all_strategies = []
        for analysis in recent_analyses:
            all_strategies.extend(analysis.successful_strategies)
            all_strategies.extend(analysis.failed_strategies)
        
        if all_strategies:
            strategy_counts = defaultdict(int)
            for strategy in all_strategies:
                strategy_counts[strategy] += 1
            
            # Find most successful strategies
            successful_strategies = [s for a in recent_analyses for s in a.successful_strategies]
            if successful_strategies:
                most_successful = max(set(successful_strategies), key=successful_strategies.count)
                recommendations.append({
                    'type': 'reinforcement',
                    'title': 'Successful Strategy',
                    'description': f'Strategy {most_successful} is working well',
                    'action': f'Increase usage of {most_successful}',
                    'priority': 7
                })
        
        return recommendations
    
    def _save_analysis(self, analysis: GameAnalysis):
        """Save game analysis to file"""
        try:
            filename = f"game_analysis_{analysis.episode}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            filepath = os.path.join(self.data_dir, filename)
            
            with open(filepath, 'w') as f:
                json.dump(asdict(analysis), f, indent=2)
                
        except Exception as e:
            print(f"❌ Error saving analysis: {e}")
    
    def get_learning_summary(self) -> Dict:
        """Get comprehensive learning summary"""
        if not self.game_analyses:
            return {"message": "No games analyzed yet"}
        
        recent_analyses = list(self.game_analyses)[-20:]  # Last 20 games
        
        return {
            "total_games": len(self.game_analyses),
            "recent_performance": {
                "win_rate": sum(1 for a in recent_analyses if a.outcome == 'victory') / len(recent_analyses),
                "avg_elixir_efficiency": np.mean([a.elixir_efficiency for a in recent_analyses]),
                "avg_damage_ratio": np.mean([a.damage_dealt / max(1, a.damage_taken) for a in recent_analyses])
            },
            "learning_insights": len(self.learning_insights),
            "recommendations": self.get_learning_recommendations(),
            "top_insights": [
                {
                    "type": insight.insight_type,
                    "description": insight.description,
                    "priority": insight.priority
                }
                for insight in sorted(self.learning_insights, key=lambda x: x.priority, reverse=True)[:5]
            ]
        }

# Supporting analysis classes
class PatternAnalyzer:
    """Analyze patterns in game data"""
    pass

class StrategyAnalyzer:
    """Analyze strategy effectiveness"""
    pass

class MistakeAnalyzer:
    """Analyze mistakes and their causes"""
    pass

class ImprovementAnalyzer:
    """Analyze improvement opportunities"""
    pass

# Example usage
def create_enhanced_learning_system():
    """Create enhanced learning system"""
    return EnhancedLearningSystem()

if __name__ == "__main__":
    # Test the enhanced learning system
    try:
        learning_system = create_enhanced_learning_system()
        print("✅ Enhanced learning system created successfully")
        
        # Test with sample game data
        sample_game_data = {
            'episode': 1,
            'total_reward': 50.0,
            'steps': 100,
            'outcome': 'victory',
            'duration': 180.0,
            'damage_dealt': 500,
            'damage_taken': 200,
            'tower_damage': 300,
            'enemy_tower_damage': 400,
            'cards_played': ['knight', 'archers'],
            'successful_strategies': ['defensive'],
            'failed_strategies': ['aggressive'],
            'enemy_patterns': ['swarm'],
            'battle_phase': 'mid',
            'enemy_deck_type': 'swarm',
            'difficulty_level': 'medium'
        }
        
        analysis = learning_system.analyze_game(sample_game_data)
        if analysis:
            print(f"✅ Game analysis completed: {analysis.outcome}")
            
            summary = learning_system.get_learning_summary()
            print(f"📊 Learning summary: {summary}")
            
            recommendations = learning_system.get_learning_recommendations()
            print(f"💡 Recommendations: {len(recommendations)}")
        
    except Exception as e:
        print(f"❌ Error testing enhanced learning system: {e}")
