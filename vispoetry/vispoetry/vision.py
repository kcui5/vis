import os
import time
import json
import requests
import pyautogui
import openai
import base64

OPENAI_KEY = "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"

pyautogui.FAILSAFE = True

#Number of seconds to move to given location
MOUSE_SPEED = 1

def get_screenshot():
    curr_time = time.strftime("%H%M%S", time.localtime())
    path = os.getcwd() + f'/screens/{curr_time}.png'
    print(f"Taking screenshot at {path}")
    ss = pyautogui.screenshot()
    ss.save(path)
    return path

def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

def vision_screenshot(img):
    """Get the GPT-4V response describing what is in the given screenshot image"""
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {OPENAI_KEY}"
    }

    payload = {
        "model": "gpt-4-vision-preview",
        "messages": [
        {
            "role": "user",
            "content": [
            {
                "type": "text",
                "text": "What's in this image? Do not try to explain what is in the image, just describe what is in it."
            },
            {
                "type": "image_url",
                "image_url": {
                "url": f"data:image/jpeg;base64,{img}"
                }
            }
            ]
        }
        ],
        "max_tokens": 300
    }

    response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload)

    res = response.json()['choices'][0]['message']['content']
    print("Screenshot description:")
    print(res)
    return res

def get_instructions(screenshot_description, task):
    """Get a list of the next three instructions for how to complete the task given the current state of the computer as a natural language description of the screenshot."""
    sys_msg = """Respond with the next three instructions for how to continue completing the given task given the current state of my computer. Respond in a numbered list of three simple and succinct instructions of how to continue completing the given task. The instructions should be basic computer inputs such as moving the mouse or hitting keys on the keyboard. Do not provide any unnecessary information such as alternative ways to complete the task, just provide each instruction precisely and succintly with each instruction as its own bullet point. For instructions involving clicking on the screen, separate the instruction into moving the mouse to the desired location and into left-clicking or right-clicking as separate bullet points."""

    user_prompt = f"The current state of my computer is as follows: {screenshot_description}. {task}"

    completion = openai.ChatCompletion.create(
    model="gpt-4",
    messages=[
        {"role": "system", "content": sys_msg},
        {"role": "user", "content": user_prompt}
    ]
    )

    instructions = completion.choices[0].message

    print("Next three instructions for task: ")
    print(task)
    print(instructions)

    l = instructions["content"].split("\n")
    return l

def move_mouse(x, y):
    """Move the mouse to the given pixel coordinates"""
    print(f"Moving to {x} {y}")
    pyautogui.moveTo(x, y, MOUSE_SPEED)
    return

def mouse_click(click):
    """Left-click the mouse"""
    print("Left-clicking mouse")
    pyautogui.click()
    return

def keyboard_type(word):
    """Type the given word"""
    print(f"Typing: {word}")
    pyautogui.typewrite(word)
    return

def get_auto_commands(instructions):
    messages = [{"role": "user", "content": instructions[0]}]
    tools = [
        {
            "type": "function",
            "function": {
                "name": "move_mouse",
                "description": "Move the mouse to the given pixel coordinates on the screen.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "x": {
                            "type": "integer",
                            "description": "The x coordinate to move the mouse to, with the origin x=0 at the top left corner of the screen. The x coordinate increases going right.",
                        },
                        "y": {
                            "type": "integer",
                            "description": "The y coordinate to move the mouse to, with the origin y=0 at the top left corner of the screen. The y coordinate increases going down."
                        },
                    },
                    "required": ["x", "y"],
                }
            }
        }, {
            "type": "function",
            "function": {
                "name": "mouse_click",
                "description": "Left click the mouse.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "click": {
                            "type": "integer",
                            "description": "An integer representation for the boolean to click. A value of one indicates the left button will be clicked."
                        }
                    },
                    "required": ["click"],
                }
            }
        }, {
            "type": "function",
            "function": {
                "name": "keyboard_type",
                "description": "Types the given string of characters on the keyboard.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "word": {
                            "type": "string",
                            "description": "The string of characters to be typed on the keyboard."
                        }
                    },
                    "required": ["word"],
                },
            },
        }
    ]
    response = openai.chat.completions.create(
        model="gpt-4-1106-preview",
        messages=messages,
        tools=tools,
        tool_choice="auto",  # auto is default, but we'll be explicit
    )
    response_message = response.choices[0].message
    tool_calls = response_message.tool_calls
    messages.append(response_message)

    if tool_calls:
        available_functions = {
            "move_mouse": move_mouse,
            "mouse_click": mouse_click,
            "type": keyboard_type
        }

        for tool_call in tool_calls:
            function_name = tool_call.function.name
            function_to_call = available_functions[function_name]
            function_args = json.loads(tool_call.function.arguments)
            
            messages.append(
                {
                    "tool_call_id": tool_call.id,
                    "role": "tool",
                    "function_to_call": function_to_call,
                    "function_args": function_args,
                }
            )
    return messages

def pause(duration=3):
    print("Sleeping...")
    time.sleep(duration)

ss_path = get_screenshot()
base64_image = encode_image(ss_path)
vision_res = vision_screenshot(base64_image)
with open("log.txt", "w") as text_file:
    text_file.write(vision_res)
pause()

task = "How can I go to amazon.com?"
instructs = get_instructions(vision_res, task)
pause()

print(get_auto_commands(instructs))