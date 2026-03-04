import os
from dotenv import load_dotenv
from openai import OpenAI
import json

import cv2
import pyautogui
import base64

load_dotenv()
client = OpenAI()

# using base64 images with gpt-4o-mini
# https://openai-hd4n6.mintlify.app/docs/guides/images#passing-a-base64-encoded-image

# Function to encode the image
def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")

img = pyautogui.screenshot()
img.save("screenshot.png")

# Path to your image
image_path = "screenshot.png"

# Getting the Base64 string
base64_image = encode_image(image_path)

query = """
You are a vision system that extracts UI element coordinates from screenshots.

Analyse this screenshot and return the following bounding boxes:

1. The bounding box of the main canvas frame (the large editable area).
2. The bounding box containing the visible text on the canvas.
3. The bounding box of the "Align centre" icon in the toolbar.

COORDINATE SYSTEM:
- Origin (0,0) is the top-left of the image.
- Format: [x_min, y_min, x_max, y_max]
- All coordinates must be integers.
- Coordinates must be in absolute pixel values.

IMPORTANT:
- Return ONLY valid JSON.
- Do NOT include explanations.
- If an element is not found, return null for that field.

Required JSON schema:

{
  "canvas_frame": [x_min, y_min, x_max, y_max] | null,
  "text_region": [x_min, y_min, x_max, y_max] | null,
  "align_centre_icon": [x_min, y_min, x_max, y_max] | null
}

"""

response = client.responses.create(
    model="gpt-4o-mini",
    input=[
        {
            "role": "user",
            "content": [
                { "type": "input_text", "text": query},
                {
                    "type": "input_image",
                    "image_url": f"data:image/jpeg;base64,{base64_image}",
                },
            ],
        }
    ],
)

print(response.output_text)

"""
The output provided by the model during testing:

```json
{
  "canvas_frame": [100, 70, 580, 420],
  "text_region": [185, 210, 419, 250],
  "align_centre_icon": [0, 0, 0, 0]
}
```

i.e. not currently very successful 

"""