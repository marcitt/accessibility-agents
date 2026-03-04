import pyautogui
import time

def focus_figma():
    """clearing sequence to ensure figma focused + no design objects selected"""
    pyautogui.press("esc")
    pyautogui.press("v")
    pyautogui.click()
    pyautogui.click()
    pyautogui.press("v")
    pyautogui.press("esc")
    
def deselect():
    pyautogui.press("v")
    pyautogui.press("esc")
    
# --- 

def plot_line(x1, y1, x2, y2, delays=0.5):    
        
    pyautogui.moveTo(x1, y1, duration=delays)
    
    focus_figma()
    
    pyautogui.press("p")
    time.sleep(delays)
    pyautogui.click()
    
    time.sleep(delays)
    
    pyautogui.moveTo(x2, y2, duration=delays)
    pyautogui.click()
    
    time.sleep(delays)
    pyautogui.hotkey("esc")
    pyautogui.moveRel(20, -20, duration=delays/2)
    
    deselect()
    
    return None


def plot_rectangle(x_start, y_start, width, height, delays=0.5):
        
    time.sleep(1)
    
    pyautogui.moveTo(x_start, y_start, duration=delays)
    
    focus_figma()
    
    pyautogui.press("r")
    
    time.sleep(delays)

    x_end = x_start+width
    y_end = y_start+height
    
    pyautogui.dragTo(x=x_end, y=y_end, duration=delays, button='left')
    pyautogui.mouseUp()
    
    time.sleep(delays)
    
    deselect()
    
    pyautogui.hotkey("esc")
    pyautogui.moveRel(20, -20, duration=delays/2)
    
    deselect()
    
    return None

def plot_bezier(b1_x,b1_y, b2_x, b2_y, ratio=0.5, l1=10, l2=10, delays=0.5):
        
    time.sleep(1)
    
    pyautogui.moveTo(b1_x, b1_y, duration=delays)
    
    focus_figma()
    
    time.sleep(delays)
    pyautogui.press("p")
    time.sleep(delays)
    pyautogui.click()
    
    time.sleep(delays)
    
    pyautogui.moveTo(b2_x, b2_y, duration=delays)
    pyautogui.click()
    
    mid_x = (b1_x * ratio) + (b2_x * (1-ratio))
    mid_y = (b1_y * ratio)+ (b2_y*(1-ratio))
    
    pyautogui.moveTo(mid_x, mid_y, duration=delays)
    
    pyautogui.keyDown('command')

    pyautogui.dragRel(l1, l2, duration=delays, button='left')
    
    pyautogui.click()
    pyautogui.keyUp('command')
    pyautogui.hotkey("esc")
    pyautogui.moveRel(20, -20, duration=delays/2)
    
    deselect()