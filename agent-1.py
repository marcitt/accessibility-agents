import os
import numpy as np
import time
import pyautogui

from dotenv import load_dotenv
from openai import OpenAI
import json

import cv2
import mss

from PIL import ImageGrab, Image
import easyocr

load_dotenv()
client = OpenAI()

def screenshot(output_path):
    """take a screenshot of monitor 1 (laptop screen)"""
    with mss.mss() as sct:
        sct_img = sct.grab(sct.monitors[1])
    img = Image.frombytes("RGB", sct_img.size, sct_img.bgra, "raw", "BGRX") # must convert from bytes to an image
    img.save(output_path)
    return img
    # this code has a high latency -> it is worth switching out for another module in future
        
def largest_onscreen_square(input_img):
    """find the largest onscreen square in a screenshot - which we assume to be the canvas"""
    gray = cv2.cvtColor(input_img, cv2.COLOR_BGR2GRAY)
    
    ret, thresh = cv2.threshold(gray, 127, 255, cv2.THRESH_BINARY) # Apply thresholding to create a binary image
    contours, hierarchy = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE) # Find contours
    # https://docs.opencv.org/3.4/d4/d73/tutorial_py_contours_begin.html

    x1, y1, w1, h1 = 0, 0, 0, 0 

    # https://www.delftstack.com/howto/python/opencv-detect-rectangle/
    # https://blog.finxter.com/5-best-ways-to-detect-a-rectangle-and-square-in-an-image-using-opencv-python/
    
    for contour in contours:
        approx = cv2.approxPolyDP(contour, 0.01 * cv2.arcLength(contour, True), True) # Approximate the contour to a polygon

        # Check if the polygon has 4 sides and is convex
        if len(approx) == 4 and cv2.isContourConvex(approx):
            
            # Calculate the bounding box of the square
            x, y, w, h = cv2.boundingRect(approx)
            
            if (w*h) > (w1*h1):
                x1, y1, w1, h1 = x, y, w, h
                
    return x1, y1, w1, h1

def define_canvas():
    
    print("taking screenshot...")
    img = screenshot("screenshot.png")
    image = cv2.imread('screenshot.png')
    
    print("finding largest onscreen square...")
    x1, y1, w1, h1 = largest_onscreen_square(image)
    cv2.rectangle(image, (x1, y1), (x1 + w1, y1 + h1), (0, 255, 0), 2)
    cv2.imwrite("identified_frame.png", image)
    crop = image[y1:y1+h1, x1:x1+w1]  
    print("isolating frame...")
    cv2.imwrite("cropped_frame.png", crop)
    
    return (x1, y1, w1, h1)

def frame_to_screen(cx, cy, fx, fy):
    """convert from canvas coordinates to screen coordinates"""
    return (cx+fx, cy+fy)

### --- Tool Calling Functions: 

def find_text_centroid(text):
    """find a central clickable point for a piece of text within a canvas"""
    
    print("identifying canvas...")
    x1, y1, w1, h1 = define_canvas()
    
    print(f"analysing canvas for {text}...")
    reader = easyocr.Reader(['en']) 
    result = reader.readtext('cropped_frame.png')

    for text_object in result:
        # only define bounding box if the text matches what we are looking for 
        if text_object[1] == text:
            bounding_box = text_object[0]
            x_sum = 0
            y_sum = 0
            
            # find midpoint:
            for x,y in bounding_box:
                x_sum += x
                y_sum += y
            x_mid = int(x_sum/len(bounding_box))
            y_mid = int(y_sum/len(bounding_box))
            # modify this later to be more efficient ...
            
            ax,ay = frame_to_screen(x1, y1, x_mid, y_mid)
            return {
                "status": "success",
                "text-identified": text_object[1],
                "text-x-coordinate": ax,
                "text-y-coordinate": ay
            } # providing the agent with a more descriptive result will help it with reasoning
            
    return {
        "status": "error",
        "message": f"{text} not found on current canvas"
    }
        
def click_design_object(x,y):
    ax = x
    ay = y
    pyautogui.moveTo(ax, ay, duration=0.5)

    # clearing sequence - needed to ensure figma is focused + no design objects are selected :
    pyautogui.press("esc")
    pyautogui.press("v")
    pyautogui.click()
    pyautogui.click()
    pyautogui.press("v")
    pyautogui.press("esc")
    # end of clearing sequence

    pyautogui.keyDown('command')   
    pyautogui.keyDown('shift')
    pyautogui.click()              
    pyautogui.keyUp('shift')
    pyautogui.keyUp('command')
    
    return {
        "status": "success",
    }
    
def click_align_centre():
    pyautogui.moveTo(1259, 706, duration=0.5) #hard-coded for now
    pyautogui.click()
    return {
        "status": "success",
    }
    
### --- Building the Agent: 
    
tools = [
    {
        "type": "function",
        "name": "click_align_centre",
        "description": "Clicks the 'align center' button",
        "parameters": {"type": "object", "properties": {}, "required": []},
    },
    {
        "type": "function",
        "name": "click_design_object",
        "description": "Clicks on a design object at a specified (x, y) coordinate.",
        "parameters": {
            "type": "object",
            "properties": {
                "x": {"type": "number"},
                "y": {"type": "number"},
            },
            "required": ["x", "y"],
        },
    },
    {
        "type": "function",
        "name": "find_text_centroid",
        "description": "Find the central coordinates of any text on the canvas.",
        "parameters": {
            "type": "object",
            "properties": {
                "text": {"type": "string", "description": "Text to locate on the canvas"},
            },
            "required": ["text"],
        },
    }
]

# system prompt - generated by gpt for gpt o_o
system_prompt = """
You are an AI assistant that interacts with a vector-based design canvas. 
The canvas contains design objects — anything on the canvas can be a design object, such as a piece of text, a line, a shape, or any other vector element. 

Important principles:

1. **Design object selection**: By default, a design object is usually not selected. Many operations (like alignment, resizing, or deleting) require the object to be selected first. You should usually assume it is not selected, and select it if needed.
2. **Operations require reasoning**: Before performing an action, you should reason about what needs to happen first. For example, to align text or a shape, you must first select the correct design object.
3. **Tool capabilities**: You have the following tools:
   - `find_text_centroid(text)`: Finds the central coordinates of a piece of text on the canvas.
   - `click_design_object(x, y)`: Clicks on a design object at the specified coordinates. Clicking selects the object.
   - `click_align_centre()`: Clicks the “align center” button to center the selected object.
4. **Vector-based assumption**: All objects are vector-based. This means positions, alignment, and selection can be addressed in terms of coordinates and clicks.
5. **Flexibility**: The user’s instructions may be ambiguous. You should reason about what actions are required to fulfill the request and the order in which to perform them.
6. **Dynamic sequencing**: Decide the correct sequence of tool calls. For example, you may need to:
   - Find the text or object
   - Select it
   - Perform the desired action (like aligning, moving, or resizing)
   Ensure that each step logically leads to completing the user’s request.
7. **Feedback handling**: You receive outputs from tool calls. Use these outputs to inform the next action. For example, after finding text coordinates, you can use them to click the object.
8. **Default assumptions**: If something is unspecified, make reasonable assumptions based on standard design workflows (e.g., selecting the object before aligning).

Your goal is to **reason about the canvas and tools** to perform the requested action safely and correctly, making use of the available tools in a logical sequence. Always consider the selection requirement before performing any operation that modifies the object.
"""

# challenge goal
question = "Change the alignment of the hello text from align left to align center"

input_list = [
    {"role": "system", "content": system_prompt},
    {"role": "user", "content": question}
]

response = client.responses.create(
    model="gpt-4o-mini",
    input=input_list,
    tools=tools,
)

MAX_STEPS = 5 #precaution to prevent expensive loops where many tokens would be wasted
steps = 0

print("\n"*100) #visually clear the terminal 
print("waiting 5 seconds before starting...")
time.sleep(5)
print("\nstarting agent...")

sleep_time = 2

# most of the required code for function calling is available here:
# https://developers.openai.com/api/docs/guides/function-calling
# however some minor adjustments needed to be made to make sure the loop worked properly 

while steps < MAX_STEPS:
    steps += 1
    
    if not response.output:
            time.sleep(sleep_time)
            print("\nNO RESPONSE")
            break
    
    tool_outputs = []
    
    for item in response.output:
        if item.type == "function_call":
            time.sleep(sleep_time)
            print(f"\nFUNCTION CALL: {item.name}")
            
            try:
                args = json.loads(item.arguments) if item.arguments else {}
            except json.JSONDecodeError:
                time.sleep(sleep_time)
                print("\nFAILED TO PARSE ARGUMENTS")
                break
            
            try:
                if item.name == "find_text_centroid":
                    result = find_text_centroid(**args)
                    
                    time.sleep(sleep_time)
                    print(f"\nfunction result: {result}")

                elif item.name == "click_design_object":
                    result = click_design_object(**args)
                    
                    time.sleep(sleep_time)
                    print(f"\nfunction result: {result}")

                elif item.name == "click_align_centre":
                    result = click_align_centre()
                    
                    time.sleep(sleep_time)
                    print(f"\nfunction result: {result}")

                else:
                    time.sleep(sleep_time)
                    print(f"\nUNKNOWN FUNCTION: {item.name}")
                    break

            except Exception as e:
                time.sleep(sleep_time)
                print(f"\nFUNCTION CALLING FAILED: {e}")
                break
            
            tool_outputs.append({
                "type": "function_call_output",
                "call_id": item.call_id,
                "output": json.dumps(result),
            })
            
        elif item.type == "message":
            time.sleep(sleep_time)
            print("\nMESSAGE:")
            print(item.content[0].text)
            break
    
        else:
            time.sleep(sleep_time)
            print(f"UNEXPECTED TYPE: {item.type}")
            break


    # suggestion from gpt was to use previous_response_id - this acts as kind of a memory?
    # then tool_outputs are used as the input for the next call
    # not super sure where the information about previous_response_id is sourced from 
    if tool_outputs:
        response = client.responses.create(
            model="gpt-4o-mini",
            previous_response_id=response.id,
            input=tool_outputs,
            tools=tools,
        )
    else:
        break