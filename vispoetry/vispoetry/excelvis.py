import pyautogui
from openai import OpenAI
import base64
import json
import time
import os
from dotenv import load_dotenv
load_dotenv()

#GPT-4V screenshot of Excel screen to ask for next step.

client = OpenAI()

GPT_4_VISION_SYSTEM_PROMPT = """
You are an expert Microsoft Excel user acting as an instructor to direct and give instructions on how to use Excel using only the keyboard.
You will be given an image taken as a screenshot from Excel along with an objective for something to do in the Excel spreadsheet.
The only allowed action space is using the keyboard to input keystrokes or keyboard shortcuts.
You should respond with the next instruction for how to complete the objective, where the instruction is very simple and consists of one atomic keyboard input.
Do not return anything other than the single instruction, do not provide additional information or descriptions.
"""

GPT_4_FUNC_CALLING_SYSTEM_PROMPT = """
You are using Microsoft Excel with only the keyboard.
Given an instruction, return the appropriate function call to execute the instruction.
"""

DEBUG_MODE = False

pyautogui.FAILSAFE = True
#Number of seconds to move to given location
MOUSE_SPEED = 1

tools = [
            {
                "type": "function",
                "function": {
                    "name": "keyboard_input",
                    "description": "The given keys recognized by the pyautogui module will be inputted. If there are multiple keys given, the individual keys will successively be held down. For example inputting 'shift' and 'right' will hold down shift then hold down right then release both.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "keys": {
                                "type": "list",
                                "description": "The list of keys to input",
                            },
                            
                        },
                        "required": ["keys"],
                    }
                }
            },
        ]

def keyboard_input(keys: list):
    """Input the given key(s). If multiple keys are given they will be successively held down."""
    print(f"Inputting keys: {keys}")
    if DEBUG_MODE:
        time.sleep(3)
        return
    for key in keys:
        pyautogui.keyDown(key)
    for key in keys[::-1]:
        pyautogui.keyUp(key)

def switch_windows():
    """Uses Cmd+Tab to switch windows"""
    print("Switching tabs...")
    pyautogui.keyDown("command")
    pyautogui.keyDown("tab")
    pyautogui.keyUp("tab")
    pyautogui.keyUp("command")
    time.sleep(1)

available_functions = {
    "keyboard_input": keyboard_input,
}

def get_screenshot():
    curr_time = time.strftime("%d %m %H%M%S", time.localtime())
    path = os.getcwd() + f'/excelscreens/{curr_time}.png'
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
    print("Received GPT-4V response: ")
    print(res_content)
    return res_content
"""
def parse_list_of_instructions(res_content):
    return res_content.split("\n")
"""
def ask_gpt_to_call_func(instruction):
    messages = [
        {"role": "system", "content": GPT_4_FUNC_CALLING_SYSTEM_PROMPT},
        {"role": "user", "content": instruction}
    ]
    completion = client.chat.completions.create(
        model="gpt-4-turbo-preview",
        messages=messages,
        tools=tools,
        tool_choice="auto",
    )
    res = completion.choices[0].message
    print("For instruction: ")
    print(instruction)
    print("Received GPT-4 function calling response: ")
    print(res)
    tool_calls = res.tool_calls
    if tool_calls:
        for tool_call in tool_calls:
            function_name = tool_call.function.name
            function_to_call = available_functions[function_name]
            function_args = json.loads(tool_call.function.arguments)
            
            if function_to_call == keyboard_input:
                function_to_call(function_args.get('keys'))
            else:
                print("Unknown function!")
    else:
        print("Did not call a function!")

def main():
    global DEBUG_MODE
    DEBUG_MODE = True
    switch_windows()
    #ss_path = get_screenshot()
    #encoded_img = encode_image(ss_path)
    task = "Break a tree wood log block."
    #instruction = ask_gpt_4v(encoded_img, task)
    #ask_gpt_to_call_func(instruction)
    print("Finished executing task: ")
    print(task)

if __name__ == "__main__":
    main()