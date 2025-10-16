
import time
import os
import pyautogui
from datetime import datetime
from Actions import Actions

class EnhancedNavigator:
    def __init__(self, actions=None):
        self.actions = actions or Actions()
        self.last_screen_state = None
        self.screen_state_count = {}
        self.navigation_history = []
        self.recovery_attempts = 0
        self.max_recovery_attempts = 3
        
        self.screen_patterns = {
            'home': self._detect_home_screen,
            'battle': self._detect_battle_screen,
            'in_match': self._detect_in_match,
            'victory': self._detect_victory_screen,
            'defeat': self._detect_defeat_screen,
            'trophy_road': self._detect_trophy_road_screen,
            'chest': self._detect_chest_screen,
            'rewards': self._detect_rewards_screen,
            'clan': self._detect_clan_screen,
            'shop': self._detect_shop_screen,
            'cards': self._detect_cards_screen,
            'loading': self._detect_loading_screen,
            'connection_error': self._detect_connection_error,
            'maintenance': self._detect_maintenance_screen
        }
        self.navigation_actions = {
            'home': self._navigate_from_home,
            'battle': self._navigate_from_battle,
            'in_match': self._handle_in_match,
            'victory': self._handle_victory_screen,
            'defeat': self._handle_defeat_screen,
            'trophy_road': self._handle_trophy_road,
            'chest': self._handle_chest_screen,
            'rewards': self._handle_rewards_screen,
            'clan': self._navigate_from_clan,
            'shop': self._navigate_from_shop,
            'cards': self._navigate_from_cards,
            'loading': self._handle_loading,
            'connection_error': self._handle_connection_error,
            'maintenance': self._handle_maintenance,
            'unknown': self._handle_unknown_screen
        }
        
    def get_current_screen(self):
        try:
            # Check each screen pattern
            for screen_name, detector in self.screen_patterns.items():
                if detector():
                    # Track screen state frequency
                    if screen_name not in self.screen_state_count:
                        self.screen_state_count[screen_name] = 0
                    self.screen_state_count[screen_name] += 1
                    
                    # Add to history
                    self.navigation_history.append({
                        'screen': screen_name,
                        'timestamp': datetime.now(),
                        'count': self.screen_state_count[screen_name]
                    })
                    
                    # Keep only last 20 history entries
                    if len(self.navigation_history) > 20:
                        self.navigation_history.pop(0)
                    
                    self.last_screen_state = screen_name
                    return screen_name
            
            # No specific screen detected
            return 'unknown'
            
        except Exception as e:
            print(f"❌ Error detecting screen: {e}")
            return 'unknown'
    
    def navigate_to_battle(self):
        """Enhanced navigation to battle with recovery"""
        try:
            print("🧭 Enhanced navigation to battle...")
            max_attempts = 15
            attempt = 0
            
            while attempt < max_attempts:
                try:
                    current_screen = self.get_current_screen()
                    print(f"📱 Current screen: {current_screen}")
                    
                    # Check if we're stuck on the same screen
                    if self._is_stuck_on_screen(current_screen):
                        print("🔄 Screen stuck detected - applying recovery...")
                        if self._apply_screen_recovery():
                            continue
                    
                    # Navigate based on current screen
                    if current_screen in self.navigation_actions:
                        result = self.navigation_actions[current_screen]()
                        if result == 'battle_started':
                            print("✅ Successfully navigated to battle!")
                            return True
                        elif result == 'continue':
                            attempt += 1
                            time.sleep(2)
                            continue
                        elif result == 'error':
                            print("❌ Navigation error, retrying...")
                            attempt += 1
                            time.sleep(3)
                            continue
                    
                    attempt += 1
                    time.sleep(2)
                    
                except Exception as e:
                    print(f"❌ Navigation error (attempt {attempt + 1}): {e}")
                    attempt += 1
                    time.sleep(3)
            
            print("⚠️ Could not navigate to battle, but continuing...")
            return False
            
        except Exception as e:
            print(f"❌ Enhanced navigation failed: {e}")
            return False
    
    def _is_stuck_on_screen(self, screen):
        """Check if we're stuck on the same screen"""
        if len(self.navigation_history) < 3:
            return False
        
        # Check if last 3 detections are the same screen
        recent_screens = [entry['screen'] for entry in self.navigation_history[-3:]]
        return all(s == screen for s in recent_screens)
    
    def _apply_screen_recovery(self):
        """Apply recovery strategies when stuck"""
        try:
            print("🔧 Applying screen recovery strategies...")
            self.recovery_attempts += 1
            
            if self.recovery_attempts > self.max_recovery_attempts:
                print("⚠️ Max recovery attempts reached")
                return False
            
            # Recovery strategy 1: Random clicks in safe areas
            print("🎯 Recovery strategy: Safe area clicks")
            safe_areas = [
                (1600, 400),  # Center
                (1400, 800),  # Bottom area
                (1800, 800),  # Bottom right
                (1200, 300),  # Top left area
            ]
            
            for x, y in safe_areas:
                try:
                    pyautogui.moveTo(x, y, duration=0.3)
                    pyautogui.click()
                    time.sleep(1)
                except Exception as e:
                    print(f"Recovery click error: {e}")
            
            # Recovery strategy 2: Escape key
            print("⌨️ Recovery strategy: Escape key")
            try:
                pyautogui.press('escape')
                time.sleep(1)
            except Exception as e:
                print(f"Escape key error: {e}")
            
            # Recovery strategy 3: Back button simulation
            print("🔙 Recovery strategy: Back navigation")
            try:
                # Try to find and click back buttons
                back_coords = [(100, 100), (50, 50), (1200, 100)]
                for x, y in back_coords:
                    pyautogui.moveTo(x, y, duration=0.2)
                    pyautogui.click()
                    time.sleep(0.5)
            except Exception as e:
                print(f"Back navigation error: {e}")
            
            time.sleep(2)
            return True
            
        except Exception as e:
            print(f"❌ Recovery strategy failed: {e}")
            return False
    
    # Screen Detection Methods
    def _detect_home_screen(self):
        """Detect if we're on the home screen"""
        try:
            # Look for home screen elements
            if hasattr(self.actions, 'detect_battle_button'):
                return self.actions.detect_battle_button()
            return False
        except:
            return False
    
    def _detect_battle_screen(self):
        """Detect battle selection screen"""
        try:
            # Look for battle selection elements
            screenshot = pyautogui.screenshot()
            # Check for battle mode selection colors/patterns
            battle_area = screenshot.crop((1300, 200, 1900, 800))
            
            # Simple color analysis for battle screen
            pixels = list(battle_area.getdata())
            blue_pixels = sum(1 for r, g, b in pixels if b > r and b > g and b > 100)
            
            return blue_pixels > 1000  # Threshold for battle screen blue colors
        except:
            return False
    
    def _detect_in_match(self):
        """Detect if we're currently in a match"""
        try:
            # Check for elixir or other in-game elements
            elixir = self.actions.count_elixir()
            return elixir is not None and elixir >= 0
        except:
            return False
    
    def _detect_victory_screen(self):
        """Detect victory screen"""
        try:
            if hasattr(self.actions, 'detect_game_end'):
                result = self.actions.detect_game_end()
                return result == 'victory'
            return False
        except:
            return False
    
    def _detect_defeat_screen(self):
        """Detect defeat screen"""
        try:
            if hasattr(self.actions, 'detect_game_end'):
                result = self.actions.detect_game_end()
                return result == 'defeat'
            return False
        except:
            return False
    
    def _detect_trophy_road_screen(self):
        """Detect Trophy Road screen"""
        try:
            if hasattr(self.actions, 'detect_trophy_road'):
                return self.actions.detect_trophy_road()
            return False
        except:
            return False
    
    def _detect_chest_screen(self):
        """Detect chest opening screen"""
        try:
            if hasattr(self.actions, 'detect_chest_screen'):
                return self.actions.detect_chest_screen()
            return False
        except:
            return False
    
    def _detect_rewards_screen(self):
        """Detect rewards/claim screen"""
        try:
            if hasattr(self.actions, 'detect_claim_button'):
                return self.actions.detect_claim_button()
            return False
        except:
            return False
    
    def _detect_clan_screen(self):
        """Detect clan screen"""
        try:
            screenshot = pyautogui.screenshot()
            # Look for clan-specific colors (purple/violet themes)
            clan_area = screenshot.crop((1200, 200, 1800, 600))
            pixels = list(clan_area.getdata())
            purple_pixels = sum(1 for r, g, b in pixels if r > 100 and b > 100 and g < 100)
            return purple_pixels > 500
        except:
            return False
    
    def _detect_shop_screen(self):
        """Detect shop screen"""
        try:
            screenshot = pyautogui.screenshot()
            # Look for shop-specific elements (golden colors)
            shop_area = screenshot.crop((1200, 200, 1800, 800))
            pixels = list(shop_area.getdata())
            gold_pixels = sum(1 for r, g, b in pixels if r > 200 and g > 150 and b < 100)
            return gold_pixels > 800
        except:
            return False
    
    def _detect_cards_screen(self):
        """Detect cards collection screen"""
        try:
            screenshot = pyautogui.screenshot()
            # Look for card grid patterns
            cards_area = screenshot.crop((1200, 300, 1800, 700))
            # Simple grid detection based on color patterns
            pixels = list(cards_area.getdata())
            varied_colors = len(set(pixels[:1000])) > 100  # Many different colors = cards
            return varied_colors
        except:
            return False
    
    def _detect_loading_screen(self):
        """Detect loading screen"""
        try:
            screenshot = pyautogui.screenshot()
            # Check for loading indicators (spinning elements, progress bars)
            center_area = screenshot.crop((1400, 400, 1600, 600))
            pixels = list(center_area.getdata())
            # Loading screens often have animated elements with varying brightness
            avg_brightness = sum(r + g + b for r, g, b in pixels) / (len(pixels) * 3)
            return avg_brightness > 150  # Bright loading screens
        except:
            return False
    
    def _detect_connection_error(self):
        """Detect connection error screen"""
        try:
            # Look for error messages or retry buttons
            screenshot = pyautogui.screenshot()
            error_area = screenshot.crop((1200, 400, 1800, 700))
            pixels = list(error_area.getdata())
            # Error screens often have red elements
            red_pixels = sum(1 for r, g, b in pixels if r > 150 and g < 100 and b < 100)
            return red_pixels > 200
        except:
            return False
    
    def _detect_maintenance_screen(self):
        """Detect maintenance screen"""
        try:
            # Similar to connection error but might have different colors
            screenshot = pyautogui.screenshot()
            maint_area = screenshot.crop((1200, 300, 1800, 800))
            # Maintenance screens often have uniform colors
            pixels = list(maint_area.getdata())
            unique_colors = len(set(pixels))
            return unique_colors < 50  # Very few colors = maintenance screen
        except:
            return False
    
    # Navigation Action Methods
    def _navigate_from_home(self):
        """Navigate from home screen to battle"""
        try:
            print("🏠 On home screen - looking for battle button")
            if hasattr(self.actions, 'detect_battle_button') and self.actions.detect_battle_button():
                if hasattr(self.actions, 'click_battle_button'):
                    self.actions.click_battle_button()
                    time.sleep(3)
                    return 'battle_started'
            return 'continue'
        except Exception as e:
            print(f"Home navigation error: {e}")
            return 'error'
    
    def _navigate_from_battle(self):
        """Navigate from battle selection to actual battle"""
        try:
            print("⚔️ On battle screen - starting battle")
            # Click in center to start battle
            pyautogui.moveTo(1600, 400, duration=0.3)
            pyautogui.click()
            time.sleep(3)
            return 'battle_started'
        except Exception as e:
            print(f"Battle selection error: {e}")
            return 'error'
    
    def _handle_in_match(self):
        """We're already in a match"""
        print("🎮 Already in match")
        return 'battle_started'
    
    def _handle_victory_screen(self):
        """Handle victory screen"""
        try:
            print("🏆 Victory screen detected")
            if hasattr(self.actions, 'click_ok_button'):
                self.actions.click_ok_button()
                time.sleep(2)
            return 'continue'
        except Exception as e:
            print(f"Victory screen error: {e}")
            return 'error'
    
    def _handle_defeat_screen(self):
        """Handle defeat screen"""
        try:
            print("💔 Defeat screen detected")
            if hasattr(self.actions, 'click_ok_button'):
                self.actions.click_ok_button()
                time.sleep(2)
            return 'continue'
        except Exception as e:
            print(f"Defeat screen error: {e}")
            return 'error'
    
    def _handle_trophy_road(self):
        """Handle Trophy Road screen"""
        try:
            print("🏆 Trophy Road screen")
            if hasattr(self.actions, 'click_trophy_road_ok'):
                self.actions.click_trophy_road_ok()
                time.sleep(3)
            return 'continue'
        except Exception as e:
            print(f"Trophy Road error: {e}")
            return 'error'
    
    def _handle_chest_screen(self):
        """Handle chest opening screen"""
        try:
            print("📦 Chest screen detected")
            if hasattr(self.actions, 'open_chest'):
                self.actions.open_chest()
                time.sleep(4)
            return 'continue'
        except Exception as e:
            print(f"Chest screen error: {e}")
            return 'error'
    
    def _handle_rewards_screen(self):
        """Handle rewards/claim screen"""
        try:
            print("🎁 Rewards screen detected")
            if hasattr(self.actions, 'click_claim_button'):
                self.actions.click_claim_button()
                time.sleep(2)
            return 'continue'
        except Exception as e:
            print(f"Rewards screen error: {e}")
            return 'error'
    
    def _navigate_from_clan(self):
        """Navigate away from clan screen"""
        try:
            print("👥 Clan screen - navigating to home")
            # Click home button (usually top-left)
            pyautogui.moveTo(100, 100, duration=0.3)
            pyautogui.click()
            time.sleep(2)
            return 'continue'
        except Exception as e:
            print(f"Clan navigation error: {e}")
            return 'error'
    
    def _navigate_from_shop(self):
        """Navigate away from shop screen"""
        try:
            print("🛒 Shop screen - navigating to home")
            # Try to find close button or navigate back
            pyautogui.press('escape')
            time.sleep(1)
            return 'continue'
        except Exception as e:
            print(f"Shop navigation error: {e}")
            return 'error'
    
    def _navigate_from_cards(self):
        """Navigate away from cards screen"""
        try:
            print("🃏 Cards screen - navigating to home")
            pyautogui.press('escape')
            time.sleep(1)
            return 'continue'
        except Exception as e:
            print(f"Cards navigation error: {e}")
            return 'error'
    
    def _handle_loading(self):
        """Handle loading screen"""
        print("⏳ Loading screen - waiting...")
        time.sleep(3)
        return 'continue'
    
    def _handle_connection_error(self):
        """Handle connection error"""
        try:
            print("🌐 Connection error - retrying")
            # Click retry or OK button
            retry_coords = [(1600, 700), (1500, 600), (1700, 600)]
            for x, y in retry_coords:
                pyautogui.moveTo(x, y, duration=0.2)
                pyautogui.click()
                time.sleep(1)
            time.sleep(5)  # Wait for connection
            return 'continue'
        except Exception as e:
            print(f"Connection error handling: {e}")
            return 'error'
    
    def _handle_maintenance(self):
        """Handle maintenance screen"""
        print("🔧 Maintenance screen - waiting...")
        time.sleep(10)  # Wait longer for maintenance
        return 'continue'
    
    def _handle_unknown_screen(self):
        """Handle unknown screen with generic actions"""
        try:
            print("❓ Unknown screen - trying generic navigation")
            
            # Try common navigation actions
            actions_to_try = [
                # Try OK button
                lambda: self.actions.click_ok_button() if hasattr(self.actions, 'click_ok_button') else False,
                # Try smart button
                lambda: self.actions.smart_button_click() if hasattr(self.actions, 'smart_button_click') else False,
                # Try escape key
                lambda: pyautogui.press('escape'),
                # Try center click
                lambda: pyautogui.click(1600, 400)
            ]
            
            for action in actions_to_try:
                try:
                    action()
                    time.sleep(2)
                    # Check if screen changed
                    new_screen = self.get_current_screen()
                    if new_screen != 'unknown':
                        print(f"✅ Screen changed to: {new_screen}")
                        return 'continue'
                except Exception as e:
                    print(f"Generic action error: {e}")
                    continue
            
            return 'error'
            
        except Exception as e:
            print(f"Unknown screen handling error: {e}")
            return 'error'
    
    def get_navigation_stats(self):
        """Get navigation statistics"""
        return {
            'screen_states': self.screen_state_count,
            'last_screen': self.last_screen_state,
            'history': self.navigation_history[-10:],  # Last 10 entries
            'recovery_attempts': self.recovery_attempts
        }