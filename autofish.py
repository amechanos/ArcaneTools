import pyautogui
import keyboard
import time
import random
import os
import sys

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
        
    for img in image_list:
        if not os.path.exists(img):
            continue
        try:
            location = pyautogui.locateOnScreen(img, confidence=confidence, grayscale=True)
            if location:
                return True
        except pyautogui.ImageNotFoundException:
            continue
        except Exception as e:
            print(f"[Warning] Error checking {img}: {e}")
            continueq
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
            while find_on_screen(CATCH_IMAGES):
                print("Waiting for UI to clear...", end="\r")
                time.sleep(0.5)
                cleanup_attempts += 1
                
                # Prevent infinite cleanup loop
                if cleanup_attempts > 20:
                    print("\n[Warning] UI not clearing, forcing continue...")
                    break

            # 2. CAST
            print("\n[Action] Casting Line...")
            w, h = pyautogui.size()
            if not safe_click(w // 2, h // 2):
                print("[ERROR] Failed to cast, retrying...")
                time.sleep(1)
                continue
            
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
                
                time.sleep(0.1)

            if not hooked:
                continue

            # 4. REEL IN
            print("[Action] Reeling in...")
            reel_start = time.time()
            click_count = 0
            
            while True:
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
                        time.sleep(1)  # Brief pause after catch
                        break
                
                # Safety: Stop reeling after 30 seconds
                if (time.time() - reel_start) > 30:
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

