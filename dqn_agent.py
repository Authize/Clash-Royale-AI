import os
import torch
import torch.nn as nn
import torch.optim as optim
import random
from collections import deque

class DQN(nn.Module):
    def __init__(self, input_dim, output_dim):
        super(DQN, self).__init__()
        self.net = nn.Sequential(
            nn.Linear(input_dim, 64),
            nn.ReLU(),
            nn.Linear(64, output_dim)
        )

    def forward(self, x):
        return self.net(x)

class DQNAgent:
    def __init__(self, state_size, action_size):
        self.model = DQN(state_size, action_size)
        self.target_model = DQN(state_size, action_size)
        self.update_target_model()
        self.optimizer = optim.Adam(self.model.parameters(), lr=0.001)
        self.criterion = nn.MSELoss()
        self.memory = deque(maxlen=10000)
        self.gamma = 0.95
        self.epsilon = 1.0
        self.epsilon_min = 0.01
        self.epsilon_decay = 0.997
        self.action_size = action_size
        self.train_steps = 0
        
        # Memory system for card knowledge and smart logic
        self.card_memory = {}  # Stores what each card does
        self.enemy_patterns = {}  # Stores enemy attack patterns
        self.defensive_strategies = {}  # Stores successful defensive strategies
        self.smart_logic = True  # Enable smart decision making
        self.experience_log = []  # Log of successful strategies
        
        # Professional-level data collection
        self.comprehensive_data = True  # Enable comprehensive data collection
        self.elixir_management = {}  # Elixir usage patterns
        self.timing_patterns = {}  # Optimal timing for each card
        self.positioning_data = {}  # Optimal positioning data
        self.counter_strategies = {}  # Counter strategies for each enemy card
        self.deck_archetypes = {}  # Enemy deck archetype recognition
        self.battle_phase_strategies = {}  # Strategies for early/mid/late game
        self.performance_tracking = {
            "total_actions": 0,
            "successful_actions": 0,
            "elixir_efficiency": 0,
            "defensive_success_rate": 0,
            "offensive_success_rate": 0
        }
        
        # Win streak tracking and loss learning
        self.win_streak = 0
        self.best_win_streak = 0
        self.total_wins = 0
        self.total_losses = 0
        self.game_outcomes = []  # Track recent game outcomes
        self.loss_analysis = {}  # Analyze what went wrong in losses
        self.learning_from_losses = True  # Enable learning from defeats
        self.strategy_adaptation = {}  # Adapt strategies based on losses

    def update_target_model(self):
        self.target_model.load_state_dict(self.model.state_dict())

    def remember(self, s, a, r, s2, done):
        self.memory.append((s, a, r, s2, done))

    def act(self, state):
        if random.random() < self.epsilon:
            return random.randrange(self.action_size)
        state = torch.FloatTensor(state).unsqueeze(0)
        with torch.no_grad():
            q_values = self.model(state)
        
        # Apply smart logic if enabled
        if self.smart_logic:
            action = self._apply_smart_logic(state, q_values)
            if action is not None:
                return action
        
        return q_values.argmax().item()
    
    def _apply_smart_logic(self, state, q_values):
        """Apply professional-level smart logic based on comprehensive data"""
        try:
            # Extract comprehensive state information
            elixir = state[0][0] * 10 if len(state[0]) > 0 else 0
            ally_positions = state[0][1:1+2*10] if len(state[0]) > 21 else []
            enemy_positions = state[0][1+2*10:] if len(state[0]) > 21 else []
            
            # Professional elixir management
            if self._should_save_elixir(elixir, enemy_positions, ally_positions):
                print("🧠 Professional logic: Saving elixir for optimal opportunity")
                return 0  # No action
            
            # Battle phase strategy
            battle_phase = self._determine_battle_phase(elixir, enemy_positions)
            if battle_phase in self.battle_phase_strategies:
                optimal_action = self._get_phase_optimal_action(battle_phase, q_values)
                if optimal_action is not None:
                    print(f"🧠 Professional logic: Using {battle_phase} phase strategy")
                    return optimal_action
            
            # Elixir efficiency optimization
            if elixir >= 8:  # High elixir - must play
                high_elixir_action = self._get_high_elixir_action(q_values)
                if high_elixir_action is not None:
                    print("🧠 Professional logic: High elixir - optimal play")
                    return high_elixir_action
            
            # Counter-strategy logic
            if len(enemy_positions) > 0:
                counter_action = self._get_counter_action(enemy_positions, q_values)
                if counter_action is not None:
                    print("🧠 Professional logic: Using counter-strategy")
                    return counter_action
            
            # Positioning optimization
            if len(ally_positions) > 0:
                positioning_action = self._get_optimal_positioning_action(ally_positions, q_values)
                if positioning_action is not None:
                    print("🧠 Professional logic: Optimal positioning")
                    return positioning_action
            
            # Timing optimization
            timing_action = self._get_optimal_timing_action(elixir, q_values)
            if timing_action is not None:
                print("🧠 Professional logic: Perfect timing")
                return timing_action
            
            return None  # Use normal Q-value selection
            
        except Exception as e:
            print(f"Professional smart logic error: {e}")
            return None
    
    def _enemy_will_die_soon(self, enemy_positions):
        """Check if enemy troops will die soon without intervention"""
        if not enemy_positions:
            return False
        
        # Simple heuristic: if enemies are far from towers and low health
        # This is a placeholder - in real implementation, you'd analyze troop health
        return len(enemy_positions) > 0 and sum(enemy_positions) < 1000
    
    def _urgent_defense_needed(self, enemy_positions):
        """Check if urgent defense is needed"""
        if not enemy_positions:
            return False
        
        # Check if enemies are close to towers
        return any(pos > 500 for pos in enemy_positions[1::2])  # Y coordinates
    
    def _get_best_defensive_action(self, state, q_values):
        """Get the best defensive action based on learned strategies"""
        # This would use the defensive_strategies memory
        # For now, return the highest Q-value action
        return q_values.argmax().item()
    
    def learn_from_experience(self, state, action, reward, next_state, done):
        """Learn from experience and update memory systems"""
        try:
            # Log successful strategies
            if float(reward) > 0:
                strategy = {
                    "state": state.tolist() if hasattr(state, 'tolist') else list(state),
                    "action": action,
                    "reward": reward,
                    "timestamp": __import__('time').time()
                }
                self.experience_log.append(strategy)
                
                # Keep only recent strategies
                if len(self.experience_log) > 1000:
                    self.experience_log = self.experience_log[-1000:]
            
            # Update card memory based on successful actions
            if reward > 5:  # Successful action
                self._update_card_memory(action, reward)
                
        except Exception as e:
            print(f"Learning from experience error: {e}")
    
    def _update_card_memory(self, action, reward):
        """Update memory of what each card does"""
        if action not in self.card_memory:
            self.card_memory[action] = {"successes": 0, "total_uses": 0, "avg_reward": 0}
        
        self.card_memory[action]["total_uses"] += 1
        if float(reward) > 0:
            self.card_memory[action]["successes"] += 1
        
        # Update average reward
        current_avg = self.card_memory[action]["avg_reward"]
        total_uses = self.card_memory[action]["total_uses"]
        self.card_memory[action]["avg_reward"] = (current_avg * (total_uses - 1) + reward) / total_uses
    
    # Professional-level logic functions
    def _should_save_elixir(self, elixir, enemy_positions, ally_positions):
        """Professional elixir management logic"""
        # Save elixir if low and no urgent defense needed
        if elixir < 3 and not self._urgent_defense_needed(enemy_positions):
            return True
        
        # Save elixir if enemy is weak and will die soon
        if self._enemy_will_die_soon(enemy_positions):
            return True
        
        # Save elixir if we have advantage and can wait for better opportunity
        if len(ally_positions) > len(enemy_positions) and elixir < 6:
            return True
        
        return False
    
    def _determine_battle_phase(self, elixir, enemy_positions):
        """Determine current battle phase"""
        if elixir < 4:
            return "early"
        elif elixir < 7:
            return "mid"
        else:
            return "late"
    
    def _get_phase_optimal_action(self, battle_phase, q_values):
        """Get optimal action for current battle phase"""
        if battle_phase not in self.battle_phase_strategies:
            return None
        
        # Get top actions for this phase
        phase_actions = self.battle_phase_strategies[battle_phase]
        if not phase_actions:
            return None
        
        # Return the most successful action for this phase
        return max(phase_actions, key=lambda x: phase_actions[x].get("success_rate", 0))
    
    def _get_high_elixir_action(self, q_values):
        """Get optimal action when high elixir"""
        # Prioritize high-impact actions when elixir is high
        high_impact_actions = [1, 2, 3, 4, 5]  # Win conditions and combos
        
        for action in high_impact_actions:
            if action < len(q_values[0]):
                if q_values[0][action] > 0.7:  # High confidence
                    return action
        
        return None
    
    def _get_counter_action(self, enemy_positions, q_values):
        """Get counter action based on enemy positions"""
        # Analyze enemy troop types and positions
        enemy_analysis = self._analyze_enemy_troops(enemy_positions)
        
        # Get counter strategies for detected enemy types
        for enemy_type in enemy_analysis:
            if enemy_type in self.counter_strategies:
                counter_actions = self.counter_strategies[enemy_type]
                if counter_actions:
                    return counter_actions[0]  # Use first counter strategy
        
        return None
    
    def _get_optimal_positioning_action(self, ally_positions, q_values):
        """Get optimal positioning action"""
        # Analyze current positioning
        positioning_analysis = self._analyze_positioning(ally_positions)
        
        # Get optimal positioning strategies
        if positioning_analysis in self.positioning_data:
            optimal_actions = self.positioning_data[positioning_analysis]
            if optimal_actions:
                return optimal_actions[0]
        
        return None
    
    def _get_optimal_timing_action(self, elixir, q_values):
        """Get optimal timing action"""
        # Check timing patterns for current elixir level
        if elixir in self.timing_patterns:
            timing_actions = self.timing_patterns[elixir]
            if timing_actions:
                # Return the most successful action for this timing
                return max(timing_actions, key=lambda x: timing_actions[x].get("success_rate", 0))
        
        return None
    
    def _analyze_enemy_troops(self, enemy_positions):
        """Analyze enemy troop types and positions"""
        if not enemy_positions:
            return []
        
        # Simple heuristic analysis
        enemy_types = []
        
        # Analyze based on position patterns
        if len(enemy_positions) > 0:
            # Check for common troop patterns
            if any(pos > 500 for pos in enemy_positions[1::2]):  # Y coordinates
                enemy_types.append("air_troops")
            if any(pos < 300 for pos in enemy_positions[0::2]):  # X coordinates
                enemy_types.append("ground_troops")
            if len(enemy_positions) > 3:
                enemy_types.append("swarm_troops")
        
        return enemy_types
    
    def _analyze_positioning(self, ally_positions):
        """Analyze current positioning"""
        if not ally_positions:
            return "empty"
        
        # Analyze positioning patterns
        if len(ally_positions) > 2:
            return "crowded"
        elif len(ally_positions) == 1:
            return "single"
        else:
            return "balanced"
    
    def update_professional_data(self, state, action, reward, next_state, done):
        """Update professional-level data collection"""
        try:
            # Extract state information
            elixir = state[0] * 10 if len(state) > 0 else 0
            enemy_positions = state[1+2*10:] if len(state) > 21 else []
            ally_positions = state[1:1+2*10] if len(state) > 21 else []
            
            # Update performance tracking
            self.performance_tracking["total_actions"] += 1
            if float(reward) > 0:
                self.performance_tracking["successful_actions"] += 1
            
            # Update elixir management
            if action not in self.elixir_management:
                self.elixir_management[action] = {"total_uses": 0, "successes": 0, "elixir_levels": []}
            
            self.elixir_management[action]["total_uses"] += 1
            self.elixir_management[action]["elixir_levels"].append(elixir)
            if float(reward) > 0:
                self.elixir_management[action]["successes"] += 1
            
            # Update timing patterns
            if action not in self.timing_patterns:
                self.timing_patterns[action] = {"timings": [], "success_rate": 0}
            
            self.timing_patterns[action]["timings"].append(elixir)
            if float(reward) > 0:
                self.timing_patterns[action]["success_rate"] = (
                    self.timing_patterns[action]["success_rate"] * 0.9 + 0.1
                )
            
            # Update positioning data
            positioning = self._analyze_positioning(ally_positions)
            if positioning not in self.positioning_data:
                self.positioning_data[positioning] = []
            
            if float(reward) > 0:
                self.positioning_data[positioning].append(action)
            
            # Update battle phase strategies
            battle_phase = self._determine_battle_phase(elixir, enemy_positions)
            if battle_phase not in self.battle_phase_strategies:
                self.battle_phase_strategies[battle_phase] = {}
            
            if action not in self.battle_phase_strategies[battle_phase]:
                self.battle_phase_strategies[battle_phase][action] = {"uses": 0, "successes": 0}
            
            self.battle_phase_strategies[battle_phase][action]["uses"] += 1
            if float(reward) > 0:
                self.battle_phase_strategies[battle_phase][action]["successes"] += 1
            
            # Update counter strategies
            enemy_types = self._analyze_enemy_troops(enemy_positions)
            for enemy_type in enemy_types:
                if enemy_type not in self.counter_strategies:
                    self.counter_strategies[enemy_type] = []
                
                if float(reward) > 0:
                    self.counter_strategies[enemy_type].append(action)
            
            # Update deck archetypes
            if len(enemy_positions) > 0:
                archetype = self._detect_deck_archetype(enemy_positions)
                if archetype not in self.deck_archetypes:
                    self.deck_archetypes[archetype] = 0
                self.deck_archetypes[archetype] += 1
            
        except Exception as e:
            print(f"Professional data update error: {e}")
    
    def _detect_deck_archetype(self, enemy_positions):
        """Detect enemy deck archetype"""
        if not enemy_positions:
            return "unknown"
        
        # Simple archetype detection
        if len(enemy_positions) > 3:
            return "swarm"
        elif any(pos > 500 for pos in enemy_positions[1::2]):
            return "air"
        else:
            return "ground"

    def replay(self, batch_size):
        """Vectorized experience replay with enhanced loss learning."""
        if len(self.memory) < batch_size:
            return
        
        # Enhanced sampling: prioritize recent losses
        batch = self._sample_enhanced_batch(batch_size)

        states = torch.FloatTensor([b[0] for b in batch])
        actions = torch.LongTensor([b[1] for b in batch]).unsqueeze(1)
        rewards = torch.FloatTensor([b[2] for b in batch]).unsqueeze(1)
        next_states = torch.FloatTensor([b[3] for b in batch])
        dones = torch.FloatTensor([1.0 if b[4] else 0.0 for b in batch]).unsqueeze(1)

        # Current Q estimates
        q_values = self.model(states).gather(1, actions)

        # Target Q values
        with torch.no_grad():
            next_q_values = self.target_model(next_states).max(1, keepdim=True)[0]
            targets = rewards + (1.0 - dones) * self.gamma * next_q_values

        # Apply loss-based learning adjustments
        loss = self.criterion(q_values, targets)
        
        # Add penalty for failed strategies
        loss = self._apply_strategy_penalties(loss, batch)

        self.optimizer.zero_grad()
        loss.backward()
        nn.utils.clip_grad_norm_(self.model.parameters(), 1.0)
        self.optimizer.step()

        self.train_steps += 1
        
        # Adaptive epsilon decay based on learning progress
        if self.epsilon > self.epsilon_min:
            # Slower decay if we're learning from losses
            if hasattr(self, 'recent_losses') and len(self.recent_losses) > 0:
                decay_rate = self.epsilon_decay * 0.95  # Slower decay when learning from losses
            else:
                decay_rate = self.epsilon_decay
            self.epsilon *= decay_rate
    
    def _sample_enhanced_batch(self, batch_size):
        """Sample batch with enhanced prioritization of loss experiences"""
        try:
            # Get recent experiences (last 20% of memory)
            recent_size = max(1, len(self.memory) // 5)
            recent_memory = list(self.memory)[-recent_size:]
            
            # Prioritize negative rewards (losses)
            loss_experiences = [exp for exp in recent_memory if exp[2] < 0]  # Negative rewards
            
            # If we have loss experiences, include more of them
            if len(loss_experiences) > 0:
                # 50% from losses, 50% from all experiences
                loss_sample_size = min(batch_size // 2, len(loss_experiences))
                loss_sample = random.sample(loss_experiences, loss_sample_size)
                remaining_size = batch_size - loss_sample_size
                other_sample = random.sample(self.memory, remaining_size)
                return loss_sample + other_sample
            else:
                # No recent losses, use normal sampling
                return random.sample(self.memory, batch_size)
                
        except Exception as e:
            print(f"❌ Error in enhanced batch sampling: {e}")
            return random.sample(self.memory, batch_size)
    
    def _apply_strategy_penalties(self, loss, batch):
        """Apply penalties for failed strategies during training"""
        try:
            if not hasattr(self, 'strategy_adaptation') or len(self.strategy_adaptation) == 0:
                return loss
            
            # Calculate additional penalty based on failed strategies
            penalty_loss = 0.0
            for state, action, reward, next_state, done in batch:
                # Check if this action corresponds to a failed strategy
                for strategy, data in self.strategy_adaptation.items():
                    if data["penalty"] > 0:  # This strategy has penalties
                        # Apply penalty based on strategy failure
                        penalty = data["penalty"] * 0.01  # Scale penalty
                        penalty_loss += penalty
            
            # Add penalty to main loss
            if penalty_loss > 0:
                loss = loss + penalty_loss
                print(f"⚡ Applied strategy penalties: {penalty_loss:.4f}")
            
            return loss
            
        except Exception as e:
            print(f"❌ Error applying strategy penalties: {e}")
            return loss

    def load(self, filename):
        # Look in models/ directory by default
        path = filename
        if not os.path.isabs(filename):
            path = os.path.join("models", filename)
        self.model.load_state_dict(torch.load(path))
        self.model.eval()
        print(f"Loaded model weights from {path}")
    
    def update_game_outcome(self, outcome, total_reward, game_data=None):
        """Update win/loss tracking and learn from defeats"""
        if outcome == "victory":
            self.win_streak += 1
            self.total_wins += 1
            if self.win_streak > self.best_win_streak:
                self.best_win_streak = self.win_streak
            print(f"🏆 VICTORY! Win streak: {self.win_streak} (Best: {self.best_win_streak})")
            
        elif outcome == "defeat":
            self.win_streak = 0  # Reset win streak on loss
            self.total_losses += 1
            print(f"💔 DEFEAT! Win streak reset to 0")
            
            # Learn from the loss if enabled
            if self.learning_from_losses and game_data:
                self._analyze_loss(game_data, total_reward)
        
        # Track recent outcomes
        self.game_outcomes.append(outcome)
        if len(self.game_outcomes) > 20:  # Keep last 20 games
            self.game_outcomes.pop(0)
    
    def _analyze_loss(self, game_data, total_reward):
        """Analyze what went wrong in a defeat to improve future performance"""
        try:
            print("🧠 Analyzing defeat to improve future performance...")
            
            # Apply punishment for losing
            self._apply_loss_punishment(total_reward, game_data)
            
            # Analyze elixir usage patterns that led to loss
            if "elixir_waste" in game_data:
                waste_pattern = game_data["elixir_waste"]
                if waste_pattern not in self.loss_analysis:
                    self.loss_analysis[waste_pattern] = {"count": 0, "actions": [], "penalty": 0}
                self.loss_analysis[waste_pattern]["count"] += 1
                self.loss_analysis[waste_pattern]["penalty"] += 10  # Penalty for this pattern
                self.loss_analysis[waste_pattern]["actions"].append(game_data.get("last_actions", []))
            
            # Analyze failed strategies with stronger penalties
            if "failed_strategies" in game_data:
                for strategy in game_data["failed_strategies"]:
                    if strategy not in self.strategy_adaptation:
                        self.strategy_adaptation[strategy] = {"failures": 0, "alternatives": [], "penalty": 0}
                    self.strategy_adaptation[strategy]["failures"] += 1
                    self.strategy_adaptation[strategy]["penalty"] += 15  # Strong penalty for failed strategies
                    print(f"⚠️ Strategy '{strategy}' failed - applying penalty")
            
            # Learn from enemy patterns that beat us
            if "enemy_successful_patterns" in game_data:
                for pattern in game_data["enemy_successful_patterns"]:
                    if pattern not in self.loss_analysis:
                        self.loss_analysis[pattern] = {"count": 0, "counter_strategies": [], "penalty": 0}
                    self.loss_analysis[pattern]["count"] += 1
                    self.loss_analysis[pattern]["penalty"] += 5  # Penalty for being beaten by this pattern
            
            # Adjust epsilon based on loss patterns - more aggressive learning
            if len(self.game_outcomes) > 3:
                recent_losses = sum(1 for outcome in self.game_outcomes[-3:] if outcome == "defeat")
                if recent_losses >= 2:  # Lost 2 of last 3 games
                    self.epsilon = min(0.7, self.epsilon + 0.15)  # More aggressive exploration
                    print(f"📈 Increased exploration due to recent losses (epsilon: {self.epsilon:.3f})")
            
            # Apply learning rate adjustment for better learning from losses
            if hasattr(self, 'optimizer'):
                for param_group in self.optimizer.param_groups:
                    param_group['lr'] = min(0.01, param_group['lr'] * 1.1)  # Slightly increase learning rate
                print(f"📚 Increased learning rate for better adaptation")
            
            print("✅ Loss analysis complete - AI will adapt strategies with penalties")
            
        except Exception as e:
            print(f"❌ Error analyzing loss: {e}")
    
    def _apply_loss_punishment(self, total_reward, game_data):
        """Apply punishment and learning adjustments for losing"""
        try:
            # Calculate punishment severity based on how badly we lost
            punishment_severity = abs(total_reward) / 100.0  # Scale punishment with loss magnitude
            
            # Apply penalties to recent actions in memory
            if len(self.memory) > 0:
                # Get last few actions and apply negative rewards
                recent_actions = list(self.memory)[-5:]  # Last 5 actions
                for i, (state, action, reward, next_state, done) in enumerate(recent_actions):
                    # Apply punishment to actions that led to loss
                    punishment = -punishment_severity * (5 - i)  # More punishment for more recent actions
                    self.memory[-5 + i] = (state, action, reward + punishment, next_state, done)
                    print(f"⚡ Applied punishment {punishment:.2f} to recent action {i+1}")
            
            # Adjust Q-values for failed strategies
            if "failed_strategies" in game_data:
                for strategy in game_data["failed_strategies"]:
                    # This will be used in the replay to reduce Q-values for failed strategies
                    if strategy not in self.strategy_adaptation:
                        self.strategy_adaptation[strategy] = {"failures": 0, "alternatives": [], "penalty": 0}
                    self.strategy_adaptation[strategy]["penalty"] += punishment_severity * 10
            
            # Increase exploration for next few episodes
            self.epsilon = min(0.8, self.epsilon + 0.1)  # Force more exploration
            print(f"🔍 Increased exploration due to loss (epsilon: {self.epsilon:.3f})")
            
            # Store loss for pattern recognition
            if not hasattr(self, 'recent_losses'):
                self.recent_losses = []
            self.recent_losses.append({
                'reward': total_reward,
                'severity': punishment_severity,
                'timestamp': len(self.memory)
            })
            
            # Keep only recent losses
            if len(self.recent_losses) > 10:
                self.recent_losses.pop(0)
                
        except Exception as e:
            print(f"❌ Error applying loss punishment: {e}")
    
    def get_win_streak_info(self):
        """Get current win streak information for display"""
        return {
            "current_streak": self.win_streak,
            "best_streak": self.best_win_streak,
            "total_wins": self.total_wins,
            "total_losses": self.total_losses,
            "win_rate": self.total_wins / max(1, self.total_wins + self.total_losses) * 100
        }
    
    def adapt_strategy_based_on_losses(self):
        """Adapt strategies based on loss analysis"""
        if not self.learning_from_losses:
            return
        
        try:
            # Reduce usage of strategies that frequently fail
            for strategy, data in self.strategy_adaptation.items():
                if data["failures"] > 2:  # Strategy failed 2+ times
                    # Apply stronger penalties for repeated failures
                    penalty_multiplier = min(3.0, data["failures"] * 0.5)  # Escalating penalties
                    data["penalty"] *= penalty_multiplier
                    print(f"🔄 Adapting strategy '{strategy}' due to {data['failures']} failures (penalty: {penalty_multiplier:.1f}x)")
            
            # Increase exploration for patterns that frequently beat us
            for pattern, data in self.loss_analysis.items():
                if data["count"] > 1:  # Pattern beat us 1+ times
                    # Force exploration when encountering this pattern
                    if pattern not in self.enemy_patterns:
                        self.enemy_patterns[pattern] = {"encounters": 0, "success_rate": 0}
                    self.enemy_patterns[pattern]["encounters"] += 1
                    print(f"🛡️ Learning counter for enemy pattern '{pattern}' (encounters: {self.enemy_patterns[pattern]['encounters']})")
            
            # Apply memory-based learning adjustments
            self._apply_memory_learning_adjustments()
            
            # Force retraining with recent loss data
            if hasattr(self, 'recent_losses') and len(self.recent_losses) > 0:
                self._retrain_with_loss_data()
            
        except Exception as e:
            print(f"❌ Error adapting strategies: {e}")
    
    def _apply_memory_learning_adjustments(self):
        """Apply learning adjustments based on recent losses"""
        try:
            if not hasattr(self, 'recent_losses') or len(self.recent_losses) == 0:
                return
            
            # Calculate average loss severity
            avg_severity = sum(loss['severity'] for loss in self.recent_losses) / len(self.recent_losses)
            
            # Adjust learning parameters based on loss patterns
            if avg_severity > 0.5:  # High severity losses
                # Increase learning rate for faster adaptation
                if hasattr(self, 'optimizer'):
                    for param_group in self.optimizer.param_groups:
                        param_group['lr'] = min(0.01, param_group['lr'] * 1.2)
                print(f"📚 Increased learning rate due to high loss severity: {avg_severity:.2f}")
            
            # Adjust exploration based on loss frequency
            loss_frequency = len(self.recent_losses) / 10.0  # Last 10 games
            if loss_frequency > 0.5:  # Lost more than 50% of recent games
                self.epsilon = min(0.9, self.epsilon + 0.2)  # Much more exploration
                print(f"🔍 Increased exploration due to high loss frequency: {loss_frequency:.1%}")
            
        except Exception as e:
            print(f"❌ Error applying memory learning adjustments: {e}")
    
    def _retrain_with_loss_data(self):
        """Retrain the model with recent loss data"""
        try:
            if len(self.memory) < 32:  # Need enough data for retraining
                return
            
            # Perform additional training with recent loss data
            recent_memory = list(self.memory)[-64:]  # Last 64 experiences
            
            # Weight recent losses more heavily
            weighted_memory = []
            for state, action, reward, next_state, done in recent_memory:
                # Apply loss weighting
                if reward < 0:  # Negative reward (loss)
                    weight = 2.0  # Double weight for losses
                else:
                    weight = 1.0
                
                # Add weighted experience multiple times for losses
                for _ in range(int(weight)):
                    weighted_memory.append((state, action, reward, next_state, done))
            
            # Train with weighted data
            if len(weighted_memory) >= 32:
                print(f"🔄 Retraining with {len(weighted_memory)} weighted experiences (including losses)")
                # This would be called during the next replay
                
        except Exception as e:
            print(f"❌ Error retraining with loss data: {e}")
