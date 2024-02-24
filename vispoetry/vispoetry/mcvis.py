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

GPT_4_VISION_SYSTEM_PROMPT = """
You are a Minecraft expert as an instructor to direct and give instructions on how to play a simplified version of Minecraft.
You will be given an image taken as a screenshot from Minecraft along with an objective for something to do in the Minecraft world.
You should respond with instructions for how to complete the objective, where the instructions are very simple and one of two options, either walk forward or click and hold the left mouse button.
The simplified version of Minecraft only has these two input actions, walking forward and clicking and holding, and you should decide how to execute them to complete the given objective based on the Minecraft world as seen by the screenshot.
"""

GPT_4_FUNC_CALLING_SYSTEM_PROMPT = """

"""

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
    """Get the GPT-4V response"""
    messages = [
        {
            "role": "system", "content": GPT_4_VISION_SYSTEM_PROMPT
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
        {"role": "system", "content": "You are playing a basic form of Minecraft. Given an instruction for something to do in Minecraft, call the appropriate function to execute the instruction."},
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
            
            if function_to_call == walk_forward:
                function_to_call(function_args.get('duration'))
            elif function_to_call == click_and_hold:
                function_to_call(function_args.get('duration'))
            else:
                print("Unknown function!")
    else:
        print("Did not call a function!")

def main():
    ss_path = get_screenshot()
    encoded_img = encode_image(ss_path)
    msg = "Given the state of the computer as seen by the image, what is the next step to close the window?"
    print(ask_gpt_4v(encoded_img, msg))

if __name__ == "__main__":
    main()