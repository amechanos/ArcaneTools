import pyautogui
import keyboard
import time
import random
import os

# CONFIG

stopHotkey = 'q'

BITE_IMAGE = 'start.png'  
CATCH_IMAGES = [
    os.path.join('ref','junk.png'), 
    os.path.join('ref','treasure.png'), 
    os.path.join('ref','sunken.png'), 
    os.path.join('ref','fish.png')
]

CONFIDENCE_LEVEL = 0.8 

SESSION_FISH = 0

# FUNCTIONS

def find_on_screen(image_list, confidence=CONFIDENCE_LEVEL):
    if isinstance(image_list, str):
        image_list = [image_list]
        
    for img in image_list:
        if not os.path.exists(img):
            continue
        try:
            if pyautogui.locateOnScreen(img, confidence=confidence, grayscale=True):
                return True
        except (pyautogui.ImageNotFoundException, Exception):
            continue
    return False

def start_fishing():
    print("[🎣] ArcaneTools Fishing Helper v1.2")
    print(f"[⚠️] Your stop key is: '{stopHotkey}'. Press it to stop the session.")

    time.sleep(5)

    while not keyboard.is_pressed(stopHotkey):
        # 1. CLEANUP
        while find_on_screen(CATCH_IMAGES):
            print("Waiting for UI to clear...", end="\r")
            time.sleep(0.5)

        # 2. CAST
        print("\n[Action] Casting Line...")
        w, h = pyautogui.size()
        pyautogui.click(w // 2, h // 2)
        
        time.sleep(2.5)

        # 3. WAIT FOR BITE 
        print("[State] Watching for fish...")
        hooked = False
        start_wait = time.time()
        
        while not hooked:
            if keyboard.is_pressed(stopHotkey): return
            
            # Safety: Recast if no bite in 60 seconds
            if (time.time() - start_wait) > 60:
                print("[Timeout] No bite. Recasting.")
                break
            
            if find_on_screen(BITE_IMAGE, confidence=0.7): 
                hooked = True
                print("[Bite] Found exclamation mark!")
            
            time.sleep(0.1)

        if not hooked: continue

        # 4. REEL
        print("[Action] Reeling...")
        while True:
            pyautogui.click()
            time.sleep(random.uniform(0.05, 0.08)) 
            
            if find_on_screen(CATCH_IMAGES):
                global SESSION_FISH
                SESSION_FISH += 1
                print(f"[🐟] Catch detected! Total caught this session: {SESSION_FISH}")
                break
            
            if keyboard.is_pressed(stopHotkey): return

if __name__ == "__main__":
    start_fishing()

