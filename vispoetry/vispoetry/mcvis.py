import pyautogui
from openai import OpenAI
import base64
import json
import time
import os
from dotenv import load_dotenv
load_dotenv()

#GPT-4V screenshot of Minecraft screen goes to state description. GPT-4 cascades
#tiers of decomposing tasks eventually into atomic instructions.
#GPT-4 self-prompts at each level

#GPT-4V screenshot of Minecraft screen to ask for next step.

client = OpenAI()

pyautogui.FAILSAFE = True
#Number of seconds to move to given location
MOUSE_SPEED = 1

#Action Space in Minecraft:
# Move forward
# Strafe left
# Strafe right
# Left Click
# Right Click
# Left Click and Hold
# Right Click and Hold
# Type 1-9
# Press 'E' to open inventory
# Press and Hold Shift
tools = [
            {
                "type": "function",
                "function": {
                    "name": "walk_forward",
                    "description": "Walk forward by pressing and holding 'w' for the specified duration.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "duration": {
                                "type": "float",
                                "description": "The duration in seconds to walk forward for.",
                            },
                            
                        },
                        "required": ["duration"],
                    }
                }
            }, {
                "type": "function",
                "function": {
                    "name": "click_and_hold",
                    "description": "Left-click the mouse and hold for the specified duration.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "duration": {
                                "type": "float",
                                "description": "The duration in seconds to hold the left-click button on the mouse for."
                            }
                        },
                        "required": ["duration"],
                    }
                }
            }, 
        ]

def walk_forward(duration: float):
    """Walk forward by pressing and holding 'w' for the specified duration."""
    print(f"Walking forward by pressing 'w' for {duration} seconds...")
    pyautogui.keyDown('w')
    time.sleep(duration)
    pyautogui.keyUp('w')

def click_and_hold(duration: float):
    """Left-click the mouse and hold for the specified duration."""
    print(f"Left-clicking the mouse and holding for {duration} seconds...")
    pyautogui.mouseDown(button='left')
    time.sleep(duration)
    pyautogui.mouseUp(button='left')

available_functions = {
    "walk_forward": walk_forward,
    "click_and_hold": click_and_hold,
}

def get_screenshot():
    curr_time = time.strftime("%d %m %H%M%S", time.localtime())
    path = os.getcwd() + f'/mcscreens/{curr_time}.png'
    print(f"Taking screenshot at {path}")
    ss = pyautogui.screenshot()
    ss.save(path)
    return path

def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')
    
def ask_gpt_4v(img, message):
    """Get the GPT-4V response describing what is in the given screenshot image"""
    messages = [
        {
            "role": "system", "content": "You are an instructor directing how to navigate the computer screen."
        },
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": message
                },
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/jpeg;base64,{img}"
                    }
                },
            ],
        },
    ]
    completion = client.chat.completions.create(
        model="gpt-4-vision-preview",
        messages=messages,
        max_tokens=300,
    )
    res_content = completion.choices[0].message.content
    
    return res_content

def ask_gpt_to_call_func(context):
    messages = [
        {"role": "system", "content": "Provide instructions based on a generic macOS setup in a theoretical scenario."},
        {"role": "user", "content": context}
    ]
    completion = client.chat.completions.create(
        model="gpt-4-turbo-preview",
        messages=messages,
        tools=tools,
        tool_choice="auto",
    )
    res = completion.choices[0].message
    tool_calls = res.tool_calls
    if tool_calls:
        for tool_call in tool_calls:
            function_name = tool_call.function.name
            function_to_call = available_functions[function_name]
            function_args = json.loads(tool_call.function.arguments)
            
            if function_to_call == move_mouse:
                function_to_call(function_args.get('x'), function_args.get('y'))
            elif function_to_call == mouse_click:
                function_to_call(function_args.get('click'))
            elif function_to_call == keyboard_type:
                function_to_call(function_args.get('word'))
            else:
                print("Unknown function!")

    

def main():
    ss_path = get_screenshot()
    encoded_img = encode_image(ss_path)
    msg = "Given the state of the computer as seen by the image, what is the next step to close the window?"
    print(ask_gpt_4v(encoded_img, msg))

if __name__ == "__main__":
    main()