#!/usr/bin/env python3
"""
Enhanced Roboflow Configuration for CRAI
Improved object detection and game state monitoring
"""

import os
import time
import numpy as np
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from inference_sdk import InferenceHTTPClient

@dataclass
class DetectionResult:
    """Structured detection result"""
    class_name: str
    confidence: float
    bbox: Tuple[float, float, float, float]  # x, y, width, height
    center: Tuple[float, float]
    area: float

@dataclass
class GameState:
    """Comprehensive game state information"""
    # Battle state
    in_battle: bool = False
    battle_phase: str = "unknown"  # early, mid, late, overtime
    time_remaining: int = 180
    
    # Tower states
    ally_king_tower_health: float = 100.0
    ally_princess_towers_health: List[float] = None
    enemy_king_tower_health: float = 100.0
    enemy_princess_towers_health: List[float] = None
    
    # Elixir management
    current_elixir: float = 0.0
    elixir_regeneration_rate: float = 1.4
    
    # Units on field
    ally_units: List[DetectionResult] = None
    enemy_units: List[DetectionResult] = None
    
    # Cards in hand
    available_cards: List[str] = None
    card_cooldowns: Dict[str, float] = None
    
    # Game outcome
    game_result: str = "ongoing"  # victory, defeat, draw, ongoing
    
    def __post_init__(self):
        if self.ally_princess_towers_health is None:
            self.ally_princess_towers_health = [100.0, 100.0]
        if self.enemy_princess_towers_health is None:
            self.enemy_princess_towers_health = [100.0, 100.0]
        if self.ally_units is None:
            self.ally_units = []
        if self.enemy_units is None:
            self.enemy_units = []
        if self.available_cards is None:
            self.available_cards = []
        if self.card_cooldowns is None:
            self.card_cooldowns = {}

class EnhancedRoboflowDetector:
    """Enhanced Roboflow detection system with improved accuracy and performance"""
    
    def __init__(self, api_key: str, workspace_troop: str, workspace_card: str, workspace_state: str = None):
        self.api_key = api_key
        self.workspace_troop = workspace_troop
        self.workspace_card = workspace_card
        self.workspace_state = workspace_state
        
        # Initialize detection clients
        self.troop_client = self._setup_client("troop")
        self.card_client = self._setup_client("card")
        if workspace_state:
            self.state_client = self._setup_client("state")
        else:
            self.state_client = None
        
        # Detection configuration
        self.confidence_threshold = 0.5
        self.nms_threshold = 0.4
        self.max_detections = 50
        
        # Performance optimization
        self.detection_cache = {}
        self.cache_duration = 0.1  # 100ms cache
        self.last_detection_time = 0
        
        # Game state tracking
        self.current_game_state = GameState()
        self.previous_detections = []
        
        # Detection classes
        self.troop_classes = [
            "knight", "archers", "giant", "skeleton", "bomber", "musketeer",
            "dragon", "wizard", "prince", "baby_dragon", "skeleton_army",
            "goblin_spear", "goblin", "valkyrie", "skeleton_giant", "witch",
            "bomber_tower", "cannon", "archer_tower", "inferno_tower", "tesla"
        ]
        
        self.card_classes = [
            "knight_card", "archers_card", "giant_card", "skeleton_card",
            "bomber_card", "musketeer_card", "dragon_card", "wizard_card",
            "prince_card", "baby_dragon_card", "skeleton_army_card",
            "goblin_spear_card", "goblin_card", "valkyrie_card", "skeleton_giant_card",
            "witch_card", "bomber_tower_card", "cannon_card", "archer_tower_card",
            "inferno_tower_card", "tesla_card", "fireball_card", "zap_card",
            "arrows_card", "tornado_card", "rocket_card", "lightning_card", "freeze_card"
        ]
        
        self.state_classes = [
            "battle_screen", "home_screen", "loading_screen", "victory_screen",
            "defeat_screen", "trophy_road", "shop_screen", "deck_screen",
            "battle_button", "ok_button", "play_again_button", "elixir_bar",
            "tower_health", "time_display", "overtime_indicator"
        ]
    
    def _setup_client(self, client_type: str) -> InferenceHTTPClient:
        """Setup Roboflow inference client"""
        try:
            api_url = os.getenv('INFERENCE_API_URL', 'http://localhost:9001').strip()
            return InferenceHTTPClient(
                api_url=api_url,
                api_key=self.api_key
            )
        except Exception as e:
            print(f"❌ Failed to setup {client_type} client: {e}")
            return None
    
    def detect_game_state(self, image_path: str) -> GameState:
        """Comprehensive game state detection"""
        try:
            # Check cache first
            current_time = time.time()
            if (current_time - self.last_detection_time) < self.cache_duration:
                return self.current_game_state
            
            # Detect different aspects of the game
            troop_detections = self._detect_troops(image_path)
            card_detections = self._detect_cards(image_path)
            state_detections = self._detect_game_state(image_path)
            
            # Update game state
            self._update_game_state(troop_detections, card_detections, state_detections)
            
            # Cache results
            self.last_detection_time = current_time
            self.detection_cache[image_path] = {
                'state': self.current_game_state,
                'timestamp': current_time
            }
            
            return self.current_game_state
            
        except Exception as e:
            print(f"❌ Error detecting game state: {e}")
            return self.current_game_state
    
    def _detect_troops(self, image_path: str) -> List[DetectionResult]:
        """Detect troops and units on the battlefield"""
        if not self.troop_client:
            return []
        
        try:
            result = self.troop_client.infer(image_path, confidence=self.confidence_threshold)
            detections = []
            
            for prediction in result.get('predictions', []):
                if prediction['confidence'] >= self.confidence_threshold:
                    detection = DetectionResult(
                        class_name=prediction['class'],
                        confidence=prediction['confidence'],
                        bbox=(
                            prediction['x'] - prediction['width'] / 2,
                            prediction['y'] - prediction['height'] / 2,
                            prediction['width'],
                            prediction['height']
                        ),
                        center=(prediction['x'], prediction['y']),
                        area=prediction['width'] * prediction['height']
                    )
                    detections.append(detection)
            
            return detections
            
        except Exception as e:
            print(f"❌ Error detecting troops: {e}")
            return []
    
    def _detect_cards(self, image_path: str) -> List[DetectionResult]:
        """Detect cards in hand"""
        if not self.card_client:
            return []
        
        try:
            result = self.card_client.infer(image_path, confidence=self.confidence_threshold)
            detections = []
            
            for prediction in result.get('predictions', []):
                if prediction['confidence'] >= self.confidence_threshold:
                    detection = DetectionResult(
                        class_name=prediction['class'],
                        confidence=prediction['confidence'],
                        bbox=(
                            prediction['x'] - prediction['width'] / 2,
                            prediction['y'] - prediction['height'] / 2,
                            prediction['width'],
                            prediction['height']
                        ),
                        center=(prediction['x'], prediction['y']),
                        area=prediction['width'] * prediction['height']
                    )
                    detections.append(detection)
            
            return detections
            
        except Exception as e:
            print(f"❌ Error detecting cards: {e}")
            return []
    
    def _detect_game_state(self, image_path: str) -> List[DetectionResult]:
        """Detect overall game state and UI elements"""
        if not self.state_client:
            return []
        
        try:
            result = self.state_client.infer(image_path, confidence=self.confidence_threshold)
            detections = []
            
            for prediction in result.get('predictions', []):
                if prediction['confidence'] >= self.confidence_threshold:
                    detection = DetectionResult(
                        class_name=prediction['class'],
                        confidence=prediction['confidence'],
                        bbox=(
                            prediction['x'] - prediction['width'] / 2,
                            prediction['y'] - prediction['height'] / 2,
                            prediction['width'],
                            prediction['height']
                        ),
                        center=(prediction['x'], prediction['y']),
                        area=prediction['width'] * prediction['height']
                    )
                    detections.append(detection)
            
            return detections
            
        except Exception as e:
            print(f"❌ Error detecting game state: {e}")
            return []
    
    def _update_game_state(self, troop_detections: List[DetectionResult], 
                          card_detections: List[DetectionResult], 
                          state_detections: List[DetectionResult]):
        """Update comprehensive game state based on detections"""
        
        # Update battle state
        self._update_battle_state(state_detections)
        
        # Update tower health
        self._update_tower_health(troop_detections, state_detections)
        
        # Update elixir state
        self._update_elixir_state(state_detections)
        
        # Update unit positions
        self._update_unit_positions(troop_detections)
        
        # Update card availability
        self._update_card_availability(card_detections)
        
        # Update game outcome
        self._update_game_outcome(state_detections)
    
    def _update_battle_state(self, state_detections: List[DetectionResult]):
        """Update battle state based on detections"""
        for detection in state_detections:
            if detection.class_name == "battle_screen":
                self.current_game_state.in_battle = True
            elif detection.class_name == "home_screen":
                self.current_game_state.in_battle = False
            elif detection.class_name == "overtime_indicator":
                self.current_game_state.battle_phase = "overtime"
            elif detection.class_name == "time_display":
                # Extract time from detection if possible
                pass
    
    def _update_tower_health(self, troop_detections: List[DetectionResult], 
                           state_detections: List[DetectionResult]):
        """Update tower health based on detections"""
        for detection in state_detections:
            if detection.class_name == "tower_health":
                # Extract health percentage from detection
                # This would need to be implemented based on specific detection logic
                pass
    
    def _update_elixir_state(self, state_detections: List[DetectionResult]):
        """Update elixir state based on detections"""
        for detection in state_detections:
            if detection.class_name == "elixir_bar":
                # Extract elixir count from detection
                # This would need to be implemented based on specific detection logic
                pass
    
    def _update_unit_positions(self, troop_detections: List[DetectionResult]):
        """Update unit positions and separate ally/enemy units"""
        self.current_game_state.ally_units = []
        self.current_game_state.enemy_units = []
        
        for detection in troop_detections:
            # Determine if unit is ally or enemy based on position
            x, y = detection.center
            if y < 400:  # Top half of screen (enemy side)
                self.current_game_state.enemy_units.append(detection)
            else:  # Bottom half of screen (ally side)
                self.current_game_state.ally_units.append(detection)
    
    def _update_card_availability(self, card_detections: List[DetectionResult]):
        """Update available cards based on detections"""
        self.current_game_state.available_cards = []
        
        for detection in card_detections:
            if detection.class_name.endswith("_card"):
                card_name = detection.class_name.replace("_card", "")
                self.current_game_state.available_cards.append(card_name)
    
    def _update_game_outcome(self, state_detections: List[DetectionResult]):
        """Update game outcome based on detections"""
        for detection in state_detections:
            if detection.class_name == "victory_screen":
                self.current_game_state.game_result = "victory"
            elif detection.class_name == "defeat_screen":
                self.current_game_state.game_result = "defeat"
    
    def get_detection_summary(self) -> Dict:
        """Get summary of current detections for AI learning"""
        return {
            "in_battle": self.current_game_state.in_battle,
            "battle_phase": self.current_game_state.battle_phase,
            "ally_units_count": len(self.current_game_state.ally_units),
            "enemy_units_count": len(self.current_game_state.enemy_units),
            "available_cards": self.current_game_state.available_cards,
            "game_result": self.current_game_state.game_result,
            "elixir": self.current_game_state.current_elixir,
            "tower_health": {
                "ally_king": self.current_game_state.ally_king_tower_health,
                "enemy_king": self.current_game_state.enemy_king_tower_health
            }
        }
    
    def optimize_detection_performance(self):
        """Optimize detection performance"""
        # Clear old cache entries
        current_time = time.time()
        self.detection_cache = {
            k: v for k, v in self.detection_cache.items() 
            if current_time - v['timestamp'] < self.cache_duration
        }
        
        # Adjust confidence threshold based on performance
        if len(self.previous_detections) > 10:
            avg_confidence = np.mean([d.confidence for d in self.previous_detections])
            if avg_confidence > 0.8:
                self.confidence_threshold = min(0.7, self.confidence_threshold + 0.05)
            elif avg_confidence < 0.6:
                self.confidence_threshold = max(0.3, self.confidence_threshold - 0.05)

# Example usage
def create_enhanced_detector():
    """Create enhanced Roboflow detector with improved configuration"""
    api_key = os.getenv('ROBOFLOW_API_KEY')
    workspace_troop = os.getenv('WORKSPACE_TROOP_DETECTION')
    workspace_card = os.getenv('WORKSPACE_CARD_DETECTION')
    
    if not all([api_key, workspace_troop, workspace_card]):
        raise ValueError("Missing required environment variables for Roboflow")
    
    return EnhancedRoboflowDetector(
        api_key=api_key,
        workspace_troop=workspace_troop,
        workspace_card=workspace_card,
        workspace_state=None  # Only use the two existing workflows
    )

if __name__ == "__main__":
    # Test the enhanced detector
    try:
        detector = create_enhanced_detector()
        print("✅ Enhanced Roboflow detector created successfully")
        print(f"📊 Troop classes: {len(detector.troop_classes)}")
        print(f"🃏 Card classes: {len(detector.card_classes)}")
        print(f"🎮 State classes: {len(detector.state_classes)}")
    except Exception as e:
        print(f"❌ Error creating enhanced detector: {e}")
