import pyautogui
import keyboard
import time
import random
import os
import sys

# Optional OpenCV/Numpy fallback for multi-scale/template matching
try:
    import cv2
    import numpy as np
    OPENCV_AVAILABLE = True
except Exception:
    OPENCV_AVAILABLE = False

# 1. This line finds exactly where your .py file is saved on the hard drive
REF_FOLDER = "ref"
script_dir = os.path.dirname(os.path.abspath(__file__))

# 2. This creates a rock-solid path to the 'ref' folder inside that directory
def get_ref(filename):
    return os.path.join(script_dir, REF_FOLDER, filename)

# 3. Define the images using the helper function
BITE_IMAGE = get_ref("start.png")
CATCH_IMAGES = [
    get_ref("junk.png"),
    get_ref("treasure.png"),
    get_ref("sunken.png"),
    get_ref("fish.png")
]

# --- STARTUP CHECK ---
print("Checking image files...")
missing = []
for img in [BITE_IMAGE] + CATCH_IMAGES:
    if not os.path.exists(img):
        missing.append(os.path.basename(img))

if missing:
    print(f"[ERROR] Still missing: {missing}")
    print(f"Expected in: {REF_FOLDER}")
else:
    print("[SUCCESS] All images loaded.")

# CONFIG
stopHotkey = 'q' # Unfortunately, the hotkey can only be a singular key/character due to keyboard library limitations. Shortcuts including shift or control will not work.
fishingRodSlot = '6' # Default slot is 6, change if needed
# Slot to temporarily switch to (switch away then back to re-equip the rod). Change if needed.
temp_switch_slot = '1'
# Delay between slot switches (seconds)
switch_delay = 0.12

CONFIDENCE_LEVEL = 0.8 
SESSION_FISH = 0

# FUNCTIONS

def validate_images():
    missing = []
    
    if not os.path.exists(BITE_IMAGE):
        missing.append(BITE_IMAGE)
    
    for img in CATCH_IMAGES:
        if not os.path.exists(img):
            missing.append(img)
    
    if missing:
        print("[ERROR] Missing image files:")
        for img in missing:
            print(f"  - {img}")
        return False
    return True

def find_on_screen(image_list, confidence=CONFIDENCE_LEVEL):
    if isinstance(image_list, str):
        image_list = [image_list]
        
    # Try a fast region-focused scan first (center area), then full-screen.
    w, h = pyautogui.size()
    # center region = center third of the screen
    cx = max(0, w // 2 - w // 6)
    cy = max(0, h // 2 - h // 6)
    cw = max(10, w // 3)
    ch = max(10, h // 3)

    for img in image_list:
        if not os.path.exists(img):
            continue

        # 1) quick region scan (center)
        try:
            try:
                loc = pyautogui.locateOnScreen(img, confidence=confidence, region=(cx, cy, cw, ch), grayscale=True)
                if loc:
                    return True
            except Exception:
                # ignore and fall back to full screen / opencv
                pass

            # 2) full-screen builtin scan
            try:
                loc = pyautogui.locateOnScreen(img, confidence=confidence, grayscale=True)
                if loc:
                    return True
            except Exception:
                pass

            # 3) OpenCV multi-scale fallback (more tolerant of size differences)
            if OPENCV_AVAILABLE:
                try:
                    # take screenshot (region if smaller search makes sense)
                    screen_img = pyautogui.screenshot()
                    screen_gray = cv2.cvtColor(np.array(screen_img), cv2.COLOR_RGB2GRAY)

                    template = cv2.imread(img, cv2.IMREAD_GRAYSCALE)
                    if template is None:
                        continue

                    th, tw = template.shape[:2]
                    # try a range of scales from smaller to larger
                    scales = [0.5, 0.6, 0.7, 0.8, 0.9, 1.0, 1.1, 1.2]
                    for scale in scales:
                        rw = int(tw * scale)
                        rh = int(th * scale)
                        if rw < 8 or rh < 8:
                            continue
                        if rw > screen_gray.shape[1] or rh > screen_gray.shape[0]:
                            continue
                        resized = cv2.resize(template, (rw, rh), interpolation=cv2.INTER_AREA)
                        res = cv2.matchTemplate(screen_gray, resized, cv2.TM_CCOEFF_NORMED)
                        _, max_val, _, _ = cv2.minMaxLoc(res)
                        if max_val >= confidence:
                            return True
                except Exception:
                    # if OpenCV fails for any reason, ignore and continue
                    pass

        except Exception as e:
            print(f"[Warning] Error checking {img}: {e}")
            continue

    return False

def safe_click(x=None, y=None):
    """Click with bounds checking"""
    try:
        w, h = pyautogui.size()
        if x is None or y is None:
            x, y = w // 2, h // 2
        
        # Ensure coordinates are within screen bounds
        x = max(0, min(x, w - 1))
        y = max(0, min(y, h - 1))
        
        pyautogui.click(x, y)
        print("clicked")
        return True
    except Exception as e:
        print(f"[ERROR] Click failed: {e}")
        return False

def start_fishing():
    global SESSION_FISH
    
    print("[🎣] ArcaneTools Fishing Helper v1.2")
    print(f"[⚠️] Stop key: '{stopHotkey}' | Starting in 5 seconds...")
    
    # Validate images exist
    if not validate_images():
        print("[ABORT] Cannot start without required images.")
        return
    
    # Add failsafe
    pyautogui.FAILSAFE = True
    print("[INFO] PyAutoGUI failsafe enabled (move mouse to corner to emergency stop)")
    
    time.sleep(5)

    try:
        while not keyboard.is_pressed(stopHotkey):
            # 1. CLEANUP - Wait for UI to clear
            cleanup_attempts = 0
            # Wait for catch UI to clear; if stuck attempt to close dialogs (ESC) a few times
            while find_on_screen(CATCH_IMAGES):
                print("Waiting for UI to clear...", end="\r")
                time.sleep(0.5)
                cleanup_attempts += 1

                # Prevent infinite cleanup loop; if it keeps failing, skip this cast to avoid repeated casting
                if cleanup_attempts > 40:
                    print("\n[Warning] UI still not clearing after multiple attempts, skipping this cast to avoid repeated casting...")
                    # Small delay to avoid immediate recast
                    time.sleep(2)
                    break

            # 2. CAST
            print("\n[Action] Casting Line...")

            # Double-check the catch UI isn't still visible before casting
            if not find_on_screen(CATCH_IMAGES):
                safe_click()
                w, h = pyautogui.size()
                
                time.sleep(2.5) 

                # 3. WAIT FOR BITE 
                print("[State] Watching for fish...")
                hooked = False
                start_wait = time.time()
                
                while not hooked:
                    if keyboard.is_pressed(stopHotkey):
                        print("\n[Stop] User requested stop.")
                        return
                    
                    # Safety: Recast if no bite in 60 seconds
                    if (time.time() - start_wait) > 60:
                        print("\n[Timeout] No bite detected in 60s. Recasting...")
                        break
                    
                    if find_on_screen(BITE_IMAGE, confidence=0.7): 
                        hooked = True
                        print("[Bite] Fish detected!")

                # 4. REEL IN
                if hooked:
                    print("[Action] Reeling in...")
                    reel_start = time.time()
                    click_count = 0
                    
                    while hooked:
                        if keyboard.is_pressed(stopHotkey):
                            print("\n[Stop] User requested stop.")
                            return
                        
                        safe_click()
                        click_count += 1
                        time.sleep(random.uniform(0.05, 0.08))
                        
                        # Check for catch every 5 clicks (reduce CPU load)
                        if click_count % 5 == 0:
                            if find_on_screen(CATCH_IMAGES):
                                    SESSION_FISH += 1
                                    print(f"[🐟] Catch #{SESSION_FISH}! Time: {time.time() - reel_start:.1f}s")
                                    hooked = False
                                    time.sleep(2)  # Brief pause after catch

                                    clear_start = time.time()

                                    # Ensure rod is re-equipped: switch away then back, then optionally recast
                                    try:
                                        print("\n[Action] Re-equipping rod to ensure it's ready...")
                                        # Switch to a temporary slot, then switch back to the rod slot
                                        keyboard.press_and_release(temp_switch_slot)
                                        time.sleep(switch_delay)
                                        keyboard.press_and_release(fishingRodSlot)
                                        time.sleep(switch_delay)
                                        # Extra brief pause to avoid accidental immediate recast
                                        time.sleep(1)

                                    except Exception as e:
                                        print(f"[Warning] Failed to re-equip rod: {e}")

                                    break
                        
                        # Safety: Stop reeling after 60 seconds
                        if (time.time() - reel_start) > 60:
                            print("[Warning] Reel timeout. Moving to next cast...")
                            break

    except KeyboardInterrupt:
        print("\n[Stop] Interrupted by user (Ctrl+C)")
    except Exception as e:
        print(f"\n[ERROR] Unexpected error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        print(f"\n[Session End] Total fish caught: {SESSION_FISH}")

if __name__ == "__main__":
    start_fishing()

