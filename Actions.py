import pyautogui
import os
from datetime import datetime
import time
import platform
import cv2
import numpy as np

class Actions:
    def __init__(self):
        self.os_type = platform.system()
        self.script_dir = os.path.dirname(os.path.abspath(__file__))
        self.images_folder = os.path.join(self.script_dir, 'main_images')
        self.buttons_images_folder = os.path.join(self.script_dir, 'images', 'buttons')

        # Define screen regions based on OS
        if self.os_type == "Darwin":  # macOS
            self.TOP_LEFT_X = 1013
            self.TOP_LEFT_Y = 120
            self.BOTTOM_RIGHT_X = 1480
            self.BOTTOM_RIGHT_Y = 683
            self.FIELD_AREA = (self.TOP_LEFT_X, self.TOP_LEFT_Y, self.BOTTOM_RIGHT_X, self.BOTTOM_RIGHT_Y)

            self.WIDTH = self.BOTTOM_RIGHT_X - self.TOP_LEFT_X
            self.HEIGHT = self.BOTTOM_RIGHT_Y - self.TOP_LEFT_Y
        elif self.os_type == "Windows": # windows
            # Try to enable DPI awareness to prevent coordinate scaling issues
            self._enable_windows_dpi_awareness()
            self.TOP_LEFT_X = 1376
            self.TOP_LEFT_Y = 120
            self.BOTTOM_RIGHT_X = 1838
            self.BOTTOM_RIGHT_Y = 769
            self.FIELD_AREA = (self.TOP_LEFT_X, self.TOP_LEFT_Y, self.BOTTOM_RIGHT_X, self.BOTTOM_RIGHT_Y)
            
            self.WIDTH = self.BOTTOM_RIGHT_X - self.TOP_LEFT_X
            self.HEIGHT = self.BOTTOM_RIGHT_Y - self.TOP_LEFT_Y
            
            # Add card bar coordinates for Windows
            self.CARD_BAR_X = 1450
            self.CARD_BAR_Y = 847
            self.CARD_BAR_WIDTH = 1862 - 1450
            self.CARD_BAR_HEIGHT = 971 - 847

        # Card position to key mapping
        self.card_keys = {
            0: '1',  # Changed from 1 to 0
            1: '2',  # Changed from 2 to 1
            2: '3',  # Changed from 3 to 2
            3: '4'   # Changed from 4 to 3
        }
        
        # Card name to position mapping (will be updated during detection)
        self.current_card_positions = {}

    def _enable_windows_dpi_awareness(self):
        try:
            import ctypes
            # First try for Windows 10+ per-monitor DPI awareness
            try:
                ctypes.windll.user32.SetProcessDpiAwarenessContext(-4)  # PER_MONITOR_AWARE_V2
                return
            except Exception:
                pass
            # Fallbacks
            try:
                ctypes.windll.shcore.SetProcessDpiAwareness(1)  # SYSTEM_AWARE
                return
            except Exception:
                pass
            try:
                ctypes.windll.user32.SetProcessDPIAware()
            except Exception:
                pass
        except Exception:
            pass

    def _resolve_image(self, candidate_names):
        """Return first existing image path from images/buttons or main_images.
        candidate_names: list of file names to try, in order of preference.
        """
        search_dirs = [self.buttons_images_folder, self.images_folder]
        for base_dir in search_dirs:
            for name in candidate_names:
                path = os.path.join(base_dir, name)
                if os.path.exists(path):
                    return path
        return None

    def _cv2_match(self, template_path, region=None, scales=None, threshold=0.75):
        """Template match using OpenCV with optional region/scales.
        Returns (x_center, y_center, width, height) on success or None.
        """
        try:
            # Grab screenshot (optionally region)
            if region:
                sx, sy, sw, sh = region
                pil_img = pyautogui.screenshot(region=(sx, sy, sw, sh))
            else:
                pil_img = pyautogui.screenshot()
            screen_bgr = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)

            # Load template
            templ = cv2.imread(template_path, cv2.IMREAD_UNCHANGED)
            if templ is None:
                return None
            if templ.ndim == 3 and templ.shape[2] == 4:
                templ = cv2.cvtColor(templ, cv2.COLOR_BGRA2BGR)

            screen_gray = cv2.cvtColor(screen_bgr, cv2.COLOR_BGR2GRAY)
            templ_gray_orig = cv2.cvtColor(templ, cv2.COLOR_BGR2GRAY)

            best_score = -1.0
            best_loc = None
            best_wh = None
            scales = scales or [1.0]
            for s in scales:
                tw = int(templ_gray_orig.shape[1] * s)
                th = int(templ_gray_orig.shape[0] * s)
                if tw < 10 or th < 10:
                    continue
                if tw >= screen_gray.shape[1] or th >= screen_gray.shape[0]:
                    continue
                templ_gray = cv2.resize(templ_gray_orig, (tw, th), interpolation=cv2.INTER_AREA)
                res = cv2.matchTemplate(screen_gray, templ_gray, cv2.TM_CCOEFF_NORMED)
                _, max_val, _, max_loc = cv2.minMaxLoc(res)
                if max_val > best_score:
                    best_score = max_val
                    best_loc = max_loc
                    best_wh = (tw, th)

            if best_score >= threshold and best_loc and best_wh:
                top_left = best_loc
                w, h = best_wh
                center_x = top_left[0] + w // 2
                center_y = top_left[1] + h // 2
                # If we searched a region, offset back to screen coords
                if region:
                    center_x += region[0]
                    center_y += region[1]
                return (center_x, center_y, w, h)
        except Exception as e:
            # Silent fallback
            print(f"CV2 match error: {e}")
        return None

    def capture_area(self, save_path):
        screenshot = pyautogui.screenshot(region=(self.TOP_LEFT_X, self.TOP_LEFT_Y, self.WIDTH, self.HEIGHT))
        screenshot.save(save_path)

    def capture_card_area(self, save_path):
        """Capture screenshot of card area"""
        screenshot = pyautogui.screenshot(region=(
            self.CARD_BAR_X, 
            self.CARD_BAR_Y, 
            self.CARD_BAR_WIDTH, 
            self.CARD_BAR_HEIGHT
        ))
        screenshot.save(save_path)

    def capture_individual_cards(self):
        """Capture and split card bar into individual card images"""
        screenshot = pyautogui.screenshot(region=(
            self.CARD_BAR_X, 
            self.CARD_BAR_Y, 
            self.CARD_BAR_WIDTH, 
            self.CARD_BAR_HEIGHT
        ))
        
        # Calculate individual card widths
        card_width = self.CARD_BAR_WIDTH // 4
        cards = []
        
        # Split into 4 individual card images
        for i in range(4):
            left = i * card_width
            card_img = screenshot.crop((left, 0, left + card_width, self.CARD_BAR_HEIGHT))
            save_path = os.path.join(self.script_dir, 'screenshots', f"card_{i+1}.png")
            card_img.save(save_path)
            cards.append(save_path)
        
        return cards

    def count_elixir(self):
        if self.os_type == "Darwin":
            for i in range(10, 0, -1):
                image_file = os.path.join(self.images_folder, f"{i}elixir.png")
                try:
                    location = pyautogui.locateOnScreen(image_file, confidence=0.5, grayscale=True)
                    if location:
                        return i
                except Exception as e:
                    print(f"Error locating {image_file}: {e}")
            return 0
        elif self.os_type == "Windows":
            target = (225, 128, 229)
            tolerance = 80
            count = 0
            for x in range(1512, 1892, 38):
                r, g, b = pyautogui.pixel(x, 989)
                if (abs(r - target[0]) <= tolerance) and (abs(g - target[1]) <= tolerance) and (abs(b - target[2]) <= tolerance):
                    count += 1
            return count
        else:
            return 0

    def update_card_positions(self, detections):
        """
        Update card positions based on detection results
        detections: list of dictionaries with 'class' and 'x' position
        """
        # Sort detections by x position (left to right)
        sorted_cards = sorted(detections, key=lambda x: x['x'])
        
        # Map cards to positions 0-3 instead of 1-4
        self.current_card_positions = {
            card['class']: idx  # Removed +1 
            for idx, card in enumerate(sorted_cards)
        }

    def card_play(self, x, y, card_index):
        print(f"Playing card {card_index} at position ({x}, {y})")
        if card_index in self.card_keys:
            key = self.card_keys[card_index]
            print(f"Pressing key: {key}")
            pyautogui.press(key)
            time.sleep(0.2)
            print(f"Moving mouse to: ({x}, {y})")
            pyautogui.moveTo(x, y, duration=0.2)
            print("Clicking")
            pyautogui.click()
        else:
            print(f"Invalid card index: {card_index}")

    def smart_button_click(self):
        """Smart button detection with priority: Battle → Claim → OK"""
        print("🔍 Smart button detection: Battle → Claim → OK")
        
        # First priority: Check for battle button
        battle_found = self.detect_battle_button()
        if battle_found:
            print("⚔️ Battle button found - clicking battle button")
            return self.click_battle_button()
        
        # Second priority: Check for Claim button
        claim_found = self.detect_claim_button()
        if claim_found:
            print("🎁 Claim button found - clicking claim button")
            return self.click_claim_button()
        
        # Third priority: Check for OK button
        ok_found = self.detect_ok_button()
        if ok_found:
            print("✅ OK button found - clicking OK button")
            return self.click_ok_button()
        
        # No buttons found
        print("❌ No Battle, Claim, or OK button found")
        return False
    
    def detect_battle_button(self):
        """Detect if there's a battle button visible"""
        try:
            print("🔍 Checking for battle button...")
            button_image = self._resolve_image([
                "battle.png", "battlestartbutton.png", "startbattle.png", "battlebutton.png"
            ])
            
            # Check if image file exists
            if not button_image:
                print("❌ Battle button image not found")
                return False
            
            confidences = [0.8, 0.7, 0.6, 0.5, 0.4, 0.3]
            
            # Define multiple regions for battle button detection
            battle_regions = [
                (1486, 755, 1730-1486, 900-755),  # Original region
                (1400, 700, 400, 300),            # Larger region
                (1300, 650, 500, 400),            # Even larger region
            ]
            
            for region in battle_regions:
                for confidence in confidences:
                    try:
                        location = pyautogui.locateOnScreen(
                            button_image,
                            confidence=confidence,
                            region=region
                        )
                        if location:
                            print(f"✅ Battle button found at {location} (confidence: {confidence})")
                            return True
                    except Exception as e:
                        print(f"Error detecting battle button: {str(e) if str(e) else 'No error message'}")
            
            print("❌ No battle button found")
            return False
            
        except Exception as e:
            print(f"❌ Error in battle button detection: {e}")
            return False
    
    def detect_ok_button(self):
        """Detect if there's an OK button visible"""
        try:
            print("🔍 Checking for OK button...")
            ok_img = self._resolve_image(["ok.png", "okbutton.png", "okay.png"]) 
            if not ok_img:
                print("OK button image not found")
                return False
            
            confidences = [0.8, 0.7, 0.6, 0.5, 0.4, 0.3, 0.2]
            
            # Search in multiple regions for OK button
            search_regions = [
                (1400, 700, 400, 200),  # Bottom right area
                (1300, 650, 500, 300),  # Slightly larger area
                (1200, 600, 600, 400),  # Even larger area
                (1000, 500, 800, 500),  # Full screen area
            ]
            
            for region in search_regions:
                for confidence in confidences:
                    try:
                        location = pyautogui.locateOnScreen(
                            ok_img, confidence=confidence, region=region
                        )
                        if location:
                            print(f"✅ OK button found at {location} (confidence: {confidence})")
                            return True
                    except Exception as e:
                        print(f"Error searching OK button: {str(e) if str(e) else 'No error message'}")
            
            # OpenCV fallback with multi-scale search over larger bottom band and full screen
            print("🔁 Falling back to OpenCV template matching for OK button...")
            cv_regions = [
                (1200, 600, 800, 480),  # Large bottom-right band
                None,                    # Full screen
            ]
            scales = [1.2, 1.0, 0.9, 0.8, 0.7]
            for region in cv_regions:
                hit = self._cv2_match(ok_img, region=region, scales=scales, threshold=0.78)
                if hit:
                    x, y, w, h = hit
                    print(f"✅ OK button found via OpenCV at center=({x},{y}) size=({w}x{h})")
                    return True
            print("❌ No OK button found")
            return False
            
        except Exception as e:
            print(f"❌ Error in OK button detection: {e}")
            return False
    
    def click_battle_button(self):
        """Click the battle button"""
        try:
            button_image = self._resolve_image([
                "battle.png", "battlestartbutton.png", "startbattle.png", "battlebutton.png"
            ])
            
            # Check if image file exists
            if not button_image:
                print("❌ Battle button image not found")
                return False
            
            confidences = [0.8, 0.7, 0.6, 0.5, 0.4, 0.3]
            
            # Define multiple regions for battle button clicking
            battle_regions = [
                (1486, 755, 1730-1486, 900-755),  # Original region
                (1400, 700, 400, 300),            # Larger region
                (1300, 650, 500, 400),            # Even larger region
            ]
            
            for region in battle_regions:
                for confidence in confidences:
                    try:
                        location = pyautogui.locateOnScreen(
                            button_image,
                            confidence=confidence,
                            region=region
                        )
                        if location:
                            x, y = pyautogui.center(location)
                            print(f"⚔️ Clicking battle button at ({x}, {y})")
                            pyautogui.moveTo(x, y, duration=0.2)
                            pyautogui.click()
                            time.sleep(1)  # Wait for battle to start
                            return True
                    except Exception as e:
                        print(f"Error clicking battle button: {str(e) if str(e) else 'No error message'}")
            
            print("❌ Failed to click battle button")
            return False
            
        except Exception as e:
            print(f"❌ Error clicking battle button: {e}")
            return False
    
    def click_ok_button(self):
        """Click the OK button"""
        try:
            ok_img = self._resolve_image(["ok.png", "okbutton.png", "okay.png"]) 
            if not ok_img:
                print("OK button image not found")
                return False
            
            confidences = [0.8, 0.7, 0.6, 0.5, 0.4, 0.3, 0.2]
            search_regions = [
                (1400, 700, 400, 200),
                (1300, 650, 500, 300),
                (1200, 600, 600, 400),
                (1000, 500, 800, 500),
            ]
            
            for region in search_regions:
                for confidence in confidences:
                    try:
                        location = pyautogui.locateOnScreen(
                            ok_img, confidence=confidence, region=region
                        )
                        if location:
                            x, y = pyautogui.center(location)
                            print(f"✅ Clicking OK button at ({x}, {y})")
                            pyautogui.moveTo(x, y, duration=0.2)
                            pyautogui.click()
                            time.sleep(1)  # Wait for screen to change
                            return True
                    except Exception as e:
                        print(f"Error clicking OK button: {str(e) if str(e) else 'No error message'}")
            
            # OpenCV fallback click
            print("🔁 Falling back to OpenCV template matching click for OK button...")
            cv_regions = [
                (1200, 600, 800, 480),  # Large bottom band
                None,                    # Full screen
            ]
            scales = [1.2, 1.0, 0.9, 0.8, 0.7]
            for region in cv_regions:
                hit = self._cv2_match(ok_img, region=region, scales=scales, threshold=0.78)
                if hit:
                    x, y, w, h = hit
                    # Bias click slightly below center to avoid top highlight mis-clicks
                    click_x = x
                    click_y = y + max(2, h // 8)
                    print(f"✅ Clicking OK (OpenCV) at ({click_x}, {click_y}) [w={w}, h={h}]")
                    pyautogui.moveTo(click_x, click_y, duration=0.2)
                    pyautogui.click()
                    time.sleep(1)
                    return True
            print("❌ Failed to click OK button")
            return False
            
        except Exception as e:
            print(f"❌ Error clicking OK button: {e}")
            return False

    def click_battle_start(self):
        """Legacy method - now uses smart button detection"""
        return self.smart_button_click()

    def detect_claim_button(self):
        """Detect if there's a Claim button visible"""
        try:
            print("🔍 Checking for Claim button...")
            claim_img = self._resolve_image([
                "claim.png", "claimbutton.png", "claim_reward.png", "collect.png"
            ])
            if not claim_img:
                print("Claim button image not found")
                return False
            confidences = [0.85, 0.8, 0.75, 0.7, 0.6, 0.5]
            search_regions = [
                (1300, 600, 600, 400),  # Bottom area
                (1200, 500, 700, 500),  # Larger bottom area
                (1000, 400, 900, 600),  # Even larger
            ]
            for region in search_regions:
                for confidence in confidences:
                    try:
                        location = pyautogui.locateOnScreen(
                            claim_img, confidence=confidence, region=region
                        )
                        if location:
                            print(f"✅ Claim button found at {location} (confidence: {confidence})")
                            return True
                    except Exception as e:
                        print(f"Error searching Claim button: {str(e) if str(e) else 'No error message'}")
            print("❌ No Claim button found")
            return False
        except Exception as e:
            print(f"❌ Error in Claim button detection: {e}")
            return False

    def click_claim_button(self):
        """Click the Claim button"""
        try:
            claim_img = self._resolve_image([
                "claim.png", "claimbutton.png", "claim_reward.png", "collect.png"
            ])
            if not claim_img:
                print("Claim button image not found")
                return False
            confidences = [0.85, 0.8, 0.75, 0.7, 0.6, 0.5]
            search_regions = [
                (1300, 600, 600, 400),
                (1200, 500, 700, 500),
                (1000, 400, 900, 600),
            ]
            for region in search_regions:
                for confidence in confidences:
                    try:
                        location = pyautogui.locateOnScreen(
                            claim_img, confidence=confidence, region=region
                        )
                        if location:
                            x, y = pyautogui.center(location)
                            print(f"🎁 Clicking Claim button at ({x}, {y})")
                            pyautogui.moveTo(x, y, duration=0.2)
                            pyautogui.click()
                            time.sleep(0.8)
                            return True
                    except Exception as e:
                        print(f"Error clicking Claim button: {str(e) if str(e) else 'No error message'}")
            print("❌ Failed to click Claim button")
            return False
        except Exception as e:
            print(f"❌ Error clicking Claim button: {e}")
            return False

    def detect_game_end(self):
        try:
            winner_img = os.path.join(self.images_folder, "Winner.png")
            ok_img = self._resolve_image(["ok.png", "okbutton.png", "okay.png"]) or os.path.join(self.images_folder, "okbutton.png")
            confidences = [0.9, 0.85, 0.8, 0.7, 0.6]

            # Region where 'Winner' text usually appears (Windows preset)
            winner_region = (1510, 121, 1678-1510, 574-121)

            winner_location = None
            for confidence in confidences:
                print(f"\nTrying 'Winner' detection (region) with confidence: {confidence}")
                try:
                    winner_location = pyautogui.locateOnScreen(
                        winner_img, confidence=confidence, grayscale=True, region=winner_region
                    )
                except Exception as e:
                    print(f"Error locating Winner in region: {str(e) if str(e) else 'No error message'}")
                if winner_location:
                    break

            # Fallback: search full screen if not found in region
            if not winner_location:
                for confidence in confidences:
                    print(f"Trying 'Winner' detection (full screen) with confidence: {confidence}")
                    try:
                        winner_location = pyautogui.locateOnScreen(
                            winner_img, confidence=confidence, grayscale=True
                        )
                    except Exception as e:
                        print(f"Error locating Winner full screen: {str(e) if str(e) else 'No error message'}")
                    if winner_location:
                        break

            if winner_location:
                _, y = pyautogui.center(winner_location)
                print(f"Found 'Winner' at y={y}")
                result = "victory" if y > 402 else "defeat"

                # Always try to click OK to exit results screen
                time.sleep(1)
                ok_clicked = False
                # Prefer a bottom band of the screen to speed up search
                ok_region = (1400, 820, 600, 260)  # x, y, w, h - adjust if your window differs
                for confidence in confidences:
                    try:
                        print(f"Looking for OK button (region, conf={confidence})")
                        ok_loc = pyautogui.locateOnScreen(
                            ok_img, confidence=confidence, grayscale=False, region=ok_region
                        )
                        if ok_loc:
                            x, y = pyautogui.center(ok_loc)
                            print(f"Clicking OK at ({x}, {y})")
                            pyautogui.moveTo(x, y, duration=0.2)
                            pyautogui.click()
                            ok_clicked = True
                            break
                    except Exception as e:
                        print(f"Error locating OK (region): {str(e) if str(e) else 'No error message'}")
                # Full-screen fallback for OK
                if not ok_clicked:
                    for confidence in confidences:
                        try:
                            print(f"Looking for OK button (full, conf={confidence})")
                            ok_loc = pyautogui.locateOnScreen(
                                ok_img, confidence=confidence, grayscale=False
                            )
                            if ok_loc:
                                x, y = pyautogui.center(ok_loc)
                                print(f"Clicking OK at ({x}, {y})")
                                pyautogui.moveTo(x, y, duration=0.2)
                                pyautogui.click()
                                ok_clicked = True
                                break
                        except Exception as e:
                            print(f"Error locating OK (full): {str(e) if str(e) else 'No error message'}")
                # Last resort: click bottom-center fallback coordinates
                if not ok_clicked:
                    fallback_x, fallback_y = 1522, 913
                    print(f"OK not found; clicking fallback at ({fallback_x}, {fallback_y})")
                    try:
                        pyautogui.moveTo(fallback_x, fallback_y, duration=0.2)
                        pyautogui.click()
                    except Exception as e:
                        print(f"Fallback click failed: {str(e) if str(e) else 'No error message'}")

                return result
        except Exception as e:
            print(f"Error in game end detection: {str(e)}")
        return None

    def detect_match_over(self):
        matchover_img = self._resolve_image(["matchover.png"]) or os.path.join(self.images_folder, "matchover.png")
        confidences = [0.8, 0.6, 0.4]
        # Define the region where the matchover image appears (adjust as needed)
        region = (1378, 335, 1808-1378, 411-335)
        for confidence in confidences:
            try:
                location = pyautogui.locateOnScreen(
                    matchover_img, confidence=confidence, grayscale=True, region=region
                )
                if location:
                    print("Match over detected!")
                    return True
            except Exception as e:
                print(f"Error locating matchover.png: {str(e) if str(e) else 'No error message'}")
        return False

    def detect_trophy_road(self):
        """Detect if there's an OK button in the bottom right area only"""
        try:
            print("Looking for OK button in bottom right area...")
            
            # Look for OK button only in bottom right area
            ok_img = self._resolve_image(["ok.png", "okbutton.png", "okay.png"]) 
            if not ok_img or not os.path.exists(ok_img):
                print("OK button image not found, using fallback detection...")
                return self._detect_trophy_road_fallback()
            
            confidences = [0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9]
            
            # Only search in bottom right area where OK button typically appears
            search_regions = [
                (1400, 700, 400, 200),  # Bottom right area
                (1300, 650, 500, 300),  # Slightly larger bottom right area
                (1200, 600, 600, 400),  # Even larger bottom right area
            ]
            
            for region in search_regions:
                for confidence in confidences:
                    try:
                        print(f"Searching bottom right area {region} (confidence: {confidence})")
                        location = pyautogui.locateOnScreen(
                            ok_img, confidence=confidence, region=region
                        )
                        if location:
                            print(f"✅ Found OK button at {location} (confidence: {confidence})")
                            return True
                    except Exception as e:
                        print(f"Error searching OK button: {str(e) if str(e) else 'No error message'}")
            
            print("No OK button found in bottom right area")
            return False
                        
        except Exception as e:
            print(f"Error detecting OK button: {e}")
            return False
    
    def _detect_trophy_road_fallback(self):
        """Fallback detection using pixel color analysis"""
        try:
            print("Using fallback Trophy Road detection...")
            screenshot = pyautogui.screenshot()
            
            # Check multiple areas for dark blue background
            check_points = [
                (1500, 200), (1500, 400), (1500, 600), (1500, 800),
                (1600, 200), (1600, 400), (1600, 600), (1600, 800),
                (1700, 200), (1700, 400), (1700, 600), (1700, 800)
            ]
            
            dark_blue_count = 0
            for x, y in check_points:
                try:
                    r, g, b = screenshot.getpixel((x, y))
                    # Check for dark blue (blue dominant, high blue value)
                    if b > r and b > g and b > 100:
                        dark_blue_count += 1
                except:
                    continue
            
            # If we find dark blue in most areas, likely Trophy Road
            if dark_blue_count >= len(check_points) // 2:
                print(f"Trophy Road detected (dark blue background: {dark_blue_count}/{len(check_points)})")
                return True
            
            print(f"Trophy Road not detected (dark blue: {dark_blue_count}/{len(check_points)})")
            return False
            
        except Exception as e:
            print(f"Error in fallback detection: {e}")
            return False

    def click_trophy_road_ok(self):
        """Click OK button in bottom right corner"""
        try:
            print("Looking for OK button in bottom right corner...")
            
            # Try to find OK button in bottom right area
            ok_img = self._resolve_image(["ok.png", "okbutton.png", "okay.png"]) 
            if not ok_img or not os.path.exists(ok_img):
                print("OK button image not found, using bottom right corner...")
                # Click in bottom right corner
                ok_x, ok_y = 1800, 1000  # Bottom right corner
                pyautogui.moveTo(ok_x, ok_y, duration=0.2)
                pyautogui.click()
                time.sleep(0.5)
                print("OK button clicked in bottom right corner")
                return True
            
            confidences = [0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9]
            
            # Search in bottom right area
            search_regions = [
                (1400, 700, 520, 380),  # Bottom right area
                (1300, 600, 620, 480),  # Larger bottom right area
                (1200, 500, 720, 580),  # Even larger bottom right area
            ]
            
            for region in search_regions:
                for confidence in confidences:
                    try:
                        print(f"Searching bottom right area {region} (confidence: {confidence})")
                        location = pyautogui.locateOnScreen(
                            ok_img, confidence=confidence, region=region
                        )
                        if location:
                            x, y = pyautogui.center(location)
                            print(f"Found OK button at ({x}, {y})")
                            pyautogui.moveTo(x, y, duration=0.2)
                            pyautogui.click()
                            time.sleep(0.5)
                            print("✅ OK button clicked successfully!")
                            return True
                    except Exception as e:
                        print(f"Error locating OK button: {str(e) if str(e) else 'No error message'}")
            
            # Fallback: click in bottom right corner
            print("OK button not found, clicking in bottom right corner...")
            ok_x, ok_y = 1800, 1000  # Bottom right corner
            pyautogui.moveTo(ok_x, ok_y, duration=0.2)
            pyautogui.click()
            time.sleep(0.5)
            print("OK button clicked in bottom right corner")
            return True
                
        except Exception as e:
            print(f"Error clicking OK button: {e}")
            return False

    def select_trophy_road_cards(self):
        """Select two cards in Trophy Road and continue"""
        try:
            print("Selecting Trophy Road cards...")
            
            # Based on the image description, the cards are side by side
            # Left card position (skeleton with hooded cloak)
            left_card_x, left_card_y = 1450, 400  # More precise positioning
            print(f"Clicking left card at ({left_card_x}, {left_card_y})")
            pyautogui.moveTo(left_card_x, left_card_y, duration=0.3)
            pyautogui.click()
            time.sleep(1.5)  # Wait a bit longer for selection to register
            
            # Right card position (skeleton with helmet and goggles)
            right_card_x, right_card_y = 1650, 400  # More precise positioning
            print(f"Clicking right card at ({right_card_x}, {right_card_y})")
            pyautogui.moveTo(right_card_x, right_card_y, duration=0.3)
            pyautogui.click()
            time.sleep(1.5)  # Wait for selection to register
            
            # Look for and click "Continue" or "Next" button
            # Based on the image, this should be at the bottom
            continue_x, continue_y = 1600, 750  # Adjusted position for continue button
            print(f"Clicking continue button at ({continue_x}, {continue_y})")
            pyautogui.moveTo(continue_x, continue_y, duration=0.3)
            pyautogui.click()
            time.sleep(2)
            
            print("Trophy Road card selection completed")
            return True
            
        except Exception as e:
            print(f"Error selecting Trophy Road cards: {e}")
            return False

    def detect_claimable_rewards(self):
        """Detect claimable rewards on Trophy Road"""
        try:
            screenshot = pyautogui.screenshot()
            
            # Look for claimable rewards (usually have a green checkmark or are highlighted)
            # Check different positions where rewards might appear
            reward_positions = [
                (400, 300),   # Top reward
                (400, 400),   # Middle reward
                (400, 500),   # Bottom reward
                (600, 300),   # Right side rewards
                (600, 400),
                (600, 500)
            ]
            
            claimable_rewards = []
            
            for x, y in reward_positions:
                # Sample pixels around the reward position
                pixels = [
                    screenshot.getpixel((x, y)),
                    screenshot.getpixel((x+20, y)),
                    screenshot.getpixel((x, y+20)),
                    screenshot.getpixel((x+20, y+20))
                ]
                
                # Look for green checkmarks or highlighted rewards
                has_green = False
                has_highlight = False
                
                for r, g, b in pixels:
                    # Green checkmark detection
                    if g > r and g > b and g > 150:
                        has_green = True
                    # Highlighted reward detection (bright colors)
                    if r > 200 or g > 200 or b > 200:
                        has_highlight = True
                
                if has_green or has_highlight:
                    claimable_rewards.append((x, y))
                    print(f"Found claimable reward at ({x}, {y})")
            
            return claimable_rewards
            
        except Exception as e:
            print(f"Error detecting claimable rewards: {e}")
            return []

    def claim_trophy_road_rewards(self):
        """Claim available rewards on Trophy Road"""
        try:
            print("Checking for claimable rewards on Trophy Road...")
            
            # Wait a moment for the screen to fully load
            time.sleep(2)
            
            # Detect claimable rewards
            claimable_rewards = self.detect_claimable_rewards()
            
            if not claimable_rewards:
                print("No claimable rewards found")
                return True
            
            # Claim each reward
            for x, y in claimable_rewards:
                print(f"Claiming reward at ({x}, {y})")
                pyautogui.moveTo(x, y, duration=0.3)
                pyautogui.click()
                time.sleep(1)  # Wait for reward to be claimed
            
            # Wait a moment for any animations
            time.sleep(2)
            
            # Click OK button to continue
            ok_x, ok_y = 1600, 750  # Typical OK button position
            print(f"Clicking OK button at ({ok_x}, {ok_y})")
            pyautogui.moveTo(ok_x, ok_y, duration=0.3)
            pyautogui.click()
            time.sleep(1)
            
            print("Trophy Road rewards claimed successfully")
            return True
            
        except Exception as e:
            print(f"Error claiming Trophy Road rewards: {e}")
            return False

    def wait_for_trophy_road(self, max_wait_time=10):
        """Wait for Trophy Road to appear before clicking OK"""
        try:
            print("Waiting for Trophy Road to appear...")
            
            start_time = time.time()
            while time.time() - start_time < max_wait_time:
                if self.detect_trophy_road():
                    print("Trophy Road appeared! Claiming rewards...")
                    return self.claim_trophy_road_rewards()
                
                time.sleep(0.5)  # Check every 0.5 seconds
            
            print("Trophy Road did not appear within timeout, clicking OK...")
            # Click OK button as fallback
            ok_x, ok_y = 1600, 750
            pyautogui.moveTo(ok_x, ok_y, duration=0.3)
            pyautogui.click()
            time.sleep(1)
            return True
            
        except Exception as e:
            print(f"Error waiting for Trophy Road: {e}")
            return False

    def detect_chest_screen(self):
        """Detect if we're on a chest opening screen"""
        try:
            # Take a screenshot to analyze
            screenshot = pyautogui.screenshot()
            
            # Check for typical chest screen elements:
            # 1. Chest in the center of the screen
            # 2. "Open" button or similar
            # 3. Different background than normal game
            
            # Sample pixels in the center area where chests typically appear
            center_pixels = [
                screenshot.getpixel((1600, 400)),  # Center of screen
                screenshot.getpixel((1500, 450)),  # Slightly left
                screenshot.getpixel((1700, 450)),  # Slightly right
                screenshot.getpixel((1600, 500)),   # Below center
            ]
            
            # Look for chest-like colors (golden, brown, or different from game background)
            chest_colors = 0
            for r, g, b in center_pixels:
                # Check for golden/brown colors typical of chests
                if (r > 100 and g > 80 and b < 100) or (r > 120 and g > 100 and b < 80):
                    chest_colors += 1
                # Also check for bright colors that might indicate a chest
                elif r > 150 or g > 150 or b > 150:
                    chest_colors += 1
            
            # Check for "Open" button or similar text
            # Look in the bottom area where buttons typically appear
            button_area_pixels = [
                screenshot.getpixel((1500, 700)),
                screenshot.getpixel((1600, 700)),
                screenshot.getpixel((1700, 700)),
            ]
            
            # Look for button-like colors (usually darker or different from background)
            has_button = False
            for r, g, b in button_area_pixels:
                if r < 100 and g < 100 and b < 100:  # Dark button
                    has_button = True
                    break
            
            if chest_colors >= 2 or has_button:
                print("Chest screen detected")
                return True
                
        except Exception as e:
            print(f"Error detecting chest screen: {e}")
        
        return False

    def open_chest(self):
        """Open chest and handle the opening sequence"""
        try:
            print("Opening chest...")
            
            # Click on the chest (usually in the center)
            chest_x, chest_y = 1600, 400  # Center of screen
            print(f"Clicking chest at ({chest_x}, {chest_y})")
            pyautogui.moveTo(chest_x, chest_y, duration=0.3)
            pyautogui.click()
            time.sleep(2)  # Wait for chest opening animation
            
            # Look for "Open" button and click it
            open_button_x, open_button_y = 1600, 700  # Typical position of open button
            print(f"Clicking open button at ({open_button_x}, {open_button_y})")
            pyautogui.moveTo(open_button_x, open_button_y, duration=0.3)
            pyautogui.click()
            time.sleep(2)  # Wait for opening sequence
            
            # Click through any rewards or animations
            # Usually need to click multiple times to get through the sequence
            for i in range(3):  # Click 3 times to get through rewards
                print(f"Clicking through rewards (click {i+1}/3)")
                pyautogui.moveTo(1600, 400, duration=0.2)
                pyautogui.click()
                time.sleep(1)
            
            # Look for "Continue" or "Done" button
            continue_x, continue_y = 1600, 750  # Typical position
            print(f"Clicking continue button at ({continue_x}, {continue_y})")
            pyautogui.moveTo(continue_x, continue_y, duration=0.3)
            pyautogui.click()
            time.sleep(1)
            
            print("Chest opening completed")
            return True
            
        except Exception as e:
            print(f"Error opening chest: {e}")
            return False