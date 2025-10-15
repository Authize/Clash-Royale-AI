import numpy as np
import time
import os
import pyautogui
import threading
from dotenv import load_dotenv
from Actions import Actions
from inference_sdk import InferenceHTTPClient

# Disable PyAutoGUI fail-safe to prevent issues with corner detection
pyautogui.FAILSAFE = False

# Load environment variables from .env file
load_dotenv()

MAX_ENEMIES = 10
MAX_ALLIES = 10

SPELL_CARDS = ["Fireball", "Zap", "Arrows", "Tornado", "Rocket", "Lightning", "Freeze"]

class ClashRoyaleEnv:
    def __init__(self):
        self.actions = Actions()
        self.rf_model = self.setup_roboflow()
        self.card_model = self.setup_card_roboflow()
        self.state_size = 1 + 2 * (MAX_ALLIES + MAX_ENEMIES)

        self.num_cards = 4
        # Allow grid resolution to be configured via environment variables for easier tuning
        try:
            self.grid_width = int(os.getenv('GRID_WIDTH', '18'))
            self.grid_height = int(os.getenv('GRID_HEIGHT', '28'))
        except Exception:
            self.grid_width = 18
            self.grid_height = 28

        self.screenshot_path = os.path.join(os.path.dirname(__file__), 'screenshots', "current.png")
        self.available_actions = self.get_available_actions()
        self.action_size = len(self.available_actions)
        self.current_cards = []

        self.game_over_flag = None
        self._endgame_thread = None
        self._endgame_thread_stop = threading.Event()

        self.prev_elixir = None
        self.prev_enemy_presence = None

        self.prev_enemy_princess_towers = None

        self.match_over_detected = False
        self.trophy_road_detected = False
        self.in_battle = False
        self.on_home_screen = False

    def setup_roboflow(self):
        api_key = os.getenv('ROBOFLOW_API_KEY')
        if not api_key:
            raise ValueError("ROBOFLOW_API_KEY environment variable is not set. Please check your .env file.")
        
        # Allow overriding the inference API URL (local server vs hosted)
        api_url = os.getenv('INFERENCE_API_URL', 'http://localhost:9001').strip()
        return InferenceHTTPClient(
            api_url=api_url,
            api_key=api_key
        )

    def setup_card_roboflow(self):
        api_key = os.getenv('ROBOFLOW_API_KEY')
        if not api_key:
            raise ValueError("ROBOFLOW_API_KEY environment variable is not set. Please check your .env file.")
        
        api_url = os.getenv('INFERENCE_API_URL', 'http://localhost:9001').strip()
        return InferenceHTTPClient(
            api_url=api_url,
            api_key=api_key
        )

    def reset(self):
        # Default to NOT auto-playing again so we always click OK and then start a fresh match
        auto_play_again = os.getenv('AUTO_PLAY_AGAIN', 'false').strip().lower() in ('1','true','yes','y')
        if auto_play_again:
            # We expect Actions.detect_game_end() to cl2ick Play Again.
            # Give the new game a moment to load.
            time.sleep(3)
        else:
            # If we exit with OK instead of Play Again, start a new match explicitly.
            try:
                # Check if we're in Trophy Road first - just click OK to skip
                if hasattr(self.actions, "detect_trophy_road") and self.actions.detect_trophy_road():
                    print("Trophy Road detected during reset, clicking OK to skip...")
                    if hasattr(self.actions, "click_trophy_road_ok"):
                        self.actions.click_trophy_road_ok()
                    # After Trophy Road, try to start a new battle
                    time.sleep(2)
                    if hasattr(self.actions, "smart_button_click"):
                        self.actions.smart_button_click()
                    else:
                        self.actions.click_battle_start()
                else:
                    # Check if we're already in a battle before clicking battle start
                    print("Checking if already in battle...")
                    time.sleep(1)  # Give time for screen to load
                    
                    # Only click battle start if we're not already in a battle
                    if not self._is_already_in_battle():
                        print("Not in battle, starting new battle...")
                        if hasattr(self.actions, "smart_button_click"):
                            self.actions.smart_button_click()
                        else:
                            self.actions.click_battle_start()
                    else:
                        print("Already in battle, skipping battle start click")
            except Exception as e:
                print(f"Warning: click_battle_start failed: {e}")
                time.sleep(2)
        self.game_over_flag = None
        self._endgame_thread_stop.clear()
        self._endgame_thread = threading.Thread(target=self._endgame_watcher, daemon=True)
        self._endgame_thread.start()
        self.prev_elixir = None
        self.prev_enemy_presence = None
        self.prev_enemy_princess_towers = self._count_enemy_princess_towers()
        self.match_over_detected = False
        self.trophy_road_detected = False
        return self._get_state()

    def close(self):
        self._endgame_thread_stop.set()
        if self._endgame_thread:
            self._endgame_thread.join()

    def _detect_screen_state(self):
        """Detect if we're on home screen, in battle, or in post-match screen"""
        try:
            # Check if we're on home screen by looking for common home screen elements
            home_screen_indicators = [
                "battle_button.png",  # Battle button
                "chest_slot.png",     # Chest slots
                "trophy_icon.png"     # Trophy icon
            ]
            
            for indicator in home_screen_indicators:
                try:
                    location = pyautogui.locateOnScreen(
                        os.path.join(self.actions.images_folder, indicator),
                        confidence=0.7,
                        grayscale=True
                    )
                    if location:
                        return "home_screen"
                except:
                    continue
            
            # Check if we're in battle by looking for battle elements
            battle_indicators = [
                "elixir_bar.png",     # Elixir bar
                "card_slot.png",      # Card slots
                "crown_icon.png"      # Crown icon
            ]
            
            for indicator in battle_indicators:
                try:
                    location = pyautogui.locateOnScreen(
                        os.path.join(self.actions.images_folder, indicator),
                        confidence=0.7,
                        grayscale=True
                    )
                    if location:
                        return "in_battle"
                except:
                    continue
            
            # Check for post-match screens
            if self.actions.detect_match_over():
                return "post_match"
                
            return "unknown"
            
        except Exception as e:
            print(f"Error detecting screen state: {e}")
            return "unknown"

    def step(self, action_index):
        # Detect current screen state
        screen_state = self._detect_screen_state()
        print(f"Current screen state: {screen_state}")
        
        # Handle different screen states
        if screen_state == "home_screen":
            print("On home screen - attempting to start battle")
            self.on_home_screen = True
            self.in_battle = False
            # Try to start a battle
            try:
                if hasattr(self.actions, "smart_button_click"):
                    self.actions.smart_button_click()
                elif hasattr(self.actions, "click_battle_start"):
                    if hasattr(self.actions, "smart_button_click"):
                        self.actions.smart_button_click()
                    else:
                        self.actions.click_battle_start()
                    time.sleep(2)  # Wait for battle to start
                    self.in_battle = True
                    self.on_home_screen = False
            except Exception as e:
                print(f"Error starting battle: {e}")
            # Return current state with small reward for attempting to start battle
            next_state = self._get_state()
            return next_state, 5, False
            
        elif screen_state == "post_match":
            print("Post-match screen detected - waiting for next game")
            self.match_over_detected = True
            self.in_battle = False
            # Force no-op action
            action_index = len(self.available_actions) - 1
            
        elif screen_state == "in_battle":
            print("In battle - proceeding with action")
            self.in_battle = True
            self.on_home_screen = False
            
        # Check for Trophy Road first - just click OK to skip
        if not self.trophy_road_detected and hasattr(self.actions, "detect_trophy_road") and self.actions.detect_trophy_road():
            print("Trophy Road detected, clicking OK to skip...")
            self.trophy_road_detected = True
            if hasattr(self.actions, "click_trophy_road_ok"):
                self.actions.click_trophy_road_ok()
            # Return current state with small reward for skipping Trophy Road
            next_state = self._get_state()
            return next_state, 10, False  # Small reward for skipping Trophy Road

        # Check for match over
        if not self.match_over_detected and hasattr(self.actions, "detect_match_over") and self.actions.detect_match_over():
            print("Match over detected (matchover.png), forcing no-op until next game.")
            self.match_over_detected = True

        # If match over, only allow no-op action (last action in list)
        if self.match_over_detected:
            action_index = len(self.available_actions) - 1  # No-op action

        if self.game_over_flag:
            done = True
            reward = self._compute_reward(self._get_state())
            result = self.game_over_flag
            if result == "victory":
                reward += 100
                print("Victory detected - ending episode")
            elif result == "defeat":
                reward -= 100
                print("Defeat detected - ending episode")
            self.match_over_detected = False  # Reset for next episode
            return self._get_state(), reward, done

        self.current_cards = self.detect_cards_in_hand()
        print("\nCurrent cards in hand:", self.current_cards)

        # If all cards are "Unknown", check if we're actually in battle
        if all(card == "Unknown" for card in self.current_cards):
            print("All cards are Unknown - checking if we're actually in battle...")
            if not self.in_battle:
                print("Not in battle - returning no-op action")
                next_state = self._get_state()
                return next_state, 0, False
            else:
                print("In battle but cards unknown - using safe center click")
                # Click in a safe area (center of screen) instead of specific coordinates
                screen_width, screen_height = pyautogui.size()
                center_x = screen_width // 2
                center_y = screen_height // 2
                pyautogui.moveTo(center_x, center_y, duration=0.2)
                pyautogui.click()
                next_state = self._get_state()
                return next_state, 0, False

        action = self.available_actions[action_index]
        card_index, x_frac, y_frac = action
        print(f"Action selected: card_index={card_index}, x_frac={x_frac:.2f}, y_frac={y_frac:.2f}")

        spell_penalty = 0

        if card_index != -1 and card_index < len(self.current_cards):
            card_name = self.current_cards[card_index]
            print(f"Attempting to play {card_name}")
            x = int(x_frac * self.actions.WIDTH) + self.actions.TOP_LEFT_X
            y = int(y_frac * self.actions.HEIGHT) + self.actions.TOP_LEFT_Y
            self.actions.card_play(x, y, card_index)
            time.sleep(1)  # You can reduce this if needed

            # --- Spell penalty logic ---
            if card_name in SPELL_CARDS:
                state = self._get_state()
                enemy_positions = []
                for i in range(1 + 2 * MAX_ALLIES, 1 + 2 * MAX_ALLIES + 2 * MAX_ENEMIES, 2):
                    ex = state[i]
                    ey = state[i + 1]
                    if ex != 0.0 or ey != 0.0:
                        ex_px = int(ex * self.actions.WIDTH)
                        ey_px = int(ey * self.actions.HEIGHT)
                        enemy_positions.append((ex_px, ey_px))
                radius = 100
                found_enemy = any((abs(ex - x) ** 2 + abs(ey - y) ** 2) ** 0.5 < radius for ex, ey in enemy_positions)
                if not found_enemy:
                    spell_penalty = -5  # Penalize for wasting spell

        # --- Princess tower reward logic ---
        current_enemy_princess_towers = self._count_enemy_princess_towers()
        princess_tower_reward = 0
        if self.prev_enemy_princess_towers is not None:
            if current_enemy_princess_towers < self.prev_enemy_princess_towers:
                princess_tower_reward = 20
        self.prev_enemy_princess_towers = current_enemy_princess_towers

        done = False
        reward = self._compute_reward(self._get_state()) + spell_penalty + princess_tower_reward
        next_state = self._get_state()
        return next_state, reward, done

    def _get_state(self):
        self.actions.capture_area(self.screenshot_path)
        elixir = self.actions.count_elixir()
        
        workspace_name = os.getenv('WORKSPACE_TROOP_DETECTION')
        if not workspace_name:
            raise ValueError("WORKSPACE_TROOP_DETECTION environment variable is not set. Please check your .env file.")
        
        results = self.rf_model.run_workflow(
            workspace_name=workspace_name,
            workflow_id="detect-count-and-visualize",
            images={"image": self.screenshot_path}
        )

        print("RAW results:", results)

        # Handle new structure: dict with "predictions" key
        predictions = []
        if isinstance(results, dict) and "predictions" in results:
            predictions = results["predictions"]
        elif isinstance(results, list) and results:
            first = results[0]
            if isinstance(first, dict) and "predictions" in first:
                predictions = first["predictions"]
        print("Predictions:", predictions)
        # If no predictions, fall back to an empty list so we still return a valid state vector
        if not predictions:
            print("WARNING: No predictions found in results; using empty detections for this frame")
            predictions = []

        # After getting 'predictions' from results:
        if isinstance(predictions, dict) and "predictions" in predictions:
            predictions = predictions["predictions"]

        print("RAW predictions:", predictions)
        print("Detected classes:", [repr(p.get("class", "")) for p in predictions if isinstance(p, dict)])

        TOWER_CLASSES = {
            "ally king tower",
            "ally princess tower",
            "enemy king tower",
            "enemy princess tower"
        }

        def normalize_class(cls):
            return cls.strip().lower() if isinstance(cls, str) else ""

        allies = [
            (p["x"], p["y"])
            for p in predictions
            if (
                isinstance(p, dict)
                and normalize_class(p.get("class", "")) not in TOWER_CLASSES
                and normalize_class(p.get("class", "")).startswith("ally")
                and "x" in p and "y" in p
            )
        ]

        enemies = [
            (p["x"], p["y"])
            for p in predictions
            if (
                isinstance(p, dict)
                and normalize_class(p.get("class", "")) not in TOWER_CLASSES
                and normalize_class(p.get("class", "")).startswith("enemy")
                and "x" in p and "y" in p
            )
        ]

        print("Allies:", allies)
        print("Enemies:", enemies)

        # Normalize positions
        def normalize(units):
            return [(x / self.actions.WIDTH, y / self.actions.HEIGHT) for x, y in units]

        # Pad or truncate to fixed length
        def pad_units(units, max_units):
            units = normalize(units)
            if len(units) < max_units:
                units += [(0.0, 0.0)] * (max_units - len(units))
            return units[:max_units]

        ally_positions = pad_units(allies, MAX_ALLIES)
        enemy_positions = pad_units(enemies, MAX_ENEMIES)

        # Flatten positions
        ally_flat = [coord for pos in ally_positions for coord in pos]
        enemy_flat = [coord for pos in enemy_positions for coord in pos]

        # Always return a valid fixed-size state vector
        state = np.array([elixir / 10.0] + ally_flat + enemy_flat, dtype=np.float32)
        return state

    def _is_already_in_battle(self):
        """Check if we're already in a battle to avoid clicking battle start unnecessarily"""
        try:
            # Check for battle indicators
            screenshot = pyautogui.screenshot()
            
            # Look for elixir counter (indicates we're in battle)
            elixir = self.actions.count_elixir()
            if elixir is not None and elixir > 0:
                print(f"Elixir detected: {elixir} - already in battle")
                return True
            
            # Check for battle UI elements
            # Look for cards in hand area
            card_area = screenshot.crop((100, 800, 400, 1000))  # Bottom area where cards appear
            # If there are cards visible, we're likely in battle
            if self._has_cards_in_hand():
                print("Cards detected in hand - already in battle")
                return True
            
            # Check for battle start button (if it's visible, we're not in battle)
            if hasattr(self.actions, "detect_battle_start_button"):
                if self.actions.detect_battle_start_button():
                    print("Battle start button visible - not in battle")
                    return False
            
            print("No clear battle indicators found - assuming not in battle")
            return False
            
        except Exception as e:
            print(f"Error checking battle status: {e}")
            return False  # If unsure, assume not in battle

    def _has_cards_in_hand(self):
        """Check if cards are visible in hand area"""
        try:
            # Simple check: look for card-like colors in hand area
            screenshot = pyautogui.screenshot()
            hand_area = screenshot.crop((100, 800, 400, 1000))
            
            # Count non-black pixels (cards have colors)
            pixels = list(hand_area.getdata())
            colored_pixels = sum(1 for r, g, b in pixels if r + g + b > 100)
            
            # If there are enough colored pixels, likely cards
            return colored_pixels > 1000
        except:
            return False

    def _compute_reward(self, state):
        if state is None:
            return 0

        elixir = state[0] * 10

        # Sum all enemy positions (not just the first)
        enemy_positions = state[1 + 2 * MAX_ALLIES:]  # All enemy x1, y1, x2, y2, ...
        # enemy_presence = sum(enemy_positions)
        enemy_presence = sum(enemy_positions[1::2]) # Only y coords so it does not bias left/right side
        
        # Base reward: penalty for enemy presence (encourages defense)
        reward = -enemy_presence * 0.5  # Reduced penalty to not overwhelm other rewards

        # DEFENSIVE REWARDS - New additions for better defense
        
        # 1. Reward for placing cards when enemies are present (defensive play)
        if enemy_presence > 0 and self.prev_elixir is not None:
            elixir_spent = self.prev_elixir - elixir
            if elixir_spent > 0:  # AI spent elixir while enemies present
                reward += 5  # Reward for defensive card placement
        
        # 2. Reward for reducing enemy presence (successful defense)
        if self.prev_enemy_presence is not None:
            enemy_reduced = self.prev_enemy_presence - enemy_presence
            if enemy_reduced > 0:
                reward += 10 * enemy_reduced  # Strong reward for successful defense
        
        # 3. Reward for elixir efficiency in defense
        if self.prev_elixir is not None and self.prev_enemy_presence is not None:
            elixir_spent = self.prev_elixir - elixir
            enemy_reduced = self.prev_enemy_presence - enemy_presence
            if elixir_spent > 0 and enemy_reduced > 0:
                reward += 3 * min(elixir_spent, enemy_reduced)  # Efficiency bonus
        
        # 4. Penalty for not defending when enemies are close to towers
        if enemy_presence > 0:
            # Check if enemies are in defensive zone (closer to our side)
            enemy_y_positions = enemy_positions[1::2]  # Only y coordinates
            close_enemies = sum(1 for y in enemy_y_positions if y > 500)  # Enemies in our half
            if close_enemies > 0:
                reward -= 2 * close_enemies  # Penalty for not defending close enemies

        self.prev_elixir = elixir
        self.prev_enemy_presence = enemy_presence

        return reward

    def detect_cards_in_hand(self):
        try:
            card_paths = self.actions.capture_individual_cards()
            print("\nTesting individual card predictions:")

            cards = []
            workspace_name = os.getenv('WORKSPACE_CARD_DETECTION')
            if not workspace_name:
                raise ValueError("WORKSPACE_CARD_DETECTION environment variable is not set. Please check your .env file.")
            
            for card_path in card_paths:
                results = self.card_model.run_workflow(
                    workspace_name=workspace_name,
                    workflow_id="custom-workflow",
                    images={"image": card_path}
                )
                # print("Card detection raw results:", results)  # Debug print

                # Fix: parse nested structure
                predictions = []
                if isinstance(results, list) and results:
                    preds_dict = results[0].get("predictions", {})
                    if isinstance(preds_dict, dict):
                        predictions = preds_dict.get("predictions", [])
                if predictions:
                    card_name = predictions[0]["class"]
                    print(f"Detected card: {card_name}")
                    cards.append(card_name)
                else:
                    print("No card detected.")
                    cards.append("Unknown")
            return cards
        except Exception as e:
            print(f"Error in detect_cards_in_hand: {e}")
            return []

    def get_available_actions(self):
        """Generate all possible actions"""
        actions = [
            [card, x / (self.grid_width - 1), y / (self.grid_height - 1)]
            for card in range(self.num_cards)
            for x in range(self.grid_width)
            for y in range(self.grid_height)
        ]
        actions.append([-1, 0, 0])  # No-op action
        return actions

    def _endgame_watcher(self):
        while not self._endgame_thread_stop.is_set():
            result = self.actions.detect_game_end()
            if result:
                self.game_over_flag = result
                break
            # Sleep a bit to avoid hammering the CPU
            time.sleep(0.5)

    def _count_enemy_princess_towers(self):
        self.actions.capture_area(self.screenshot_path)
        
        workspace_name = os.getenv('WORKSPACE_TROOP_DETECTION')
        if not workspace_name:
            raise ValueError("WORKSPACE_TROOP_DETECTION environment variable is not set. Please check your .env file.")
        
        results = self.rf_model.run_workflow(
            workspace_name=workspace_name,
            workflow_id="detect-count-and-visualize",
            images={"image": self.screenshot_path}
        )
        predictions = []
        if isinstance(results, dict) and "predictions" in results:
            predictions = results["predictions"]
        elif isinstance(results, list) and results:
            first = results[0]
            if isinstance(first, dict) and "predictions" in first:
                predictions = first["predictions"]
        return sum(1 for p in predictions if isinstance(p, dict) and p.get("class") == "enemy princess tower")
