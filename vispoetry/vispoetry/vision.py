import os
from dotenv import load_dotenv
import time
import json
import requests
import pyautogui
import openai
import replicate
import base64

load_dotenv()
OPENAI_KEY = os.environ.get("OPENAI_KEY")
REPLICATE_KEY = os.environ.get("REPLICATE_API_TOKEN")

openai.api_key = OPENAI_KEY

pyautogui.FAILSAFE = True

#Number of seconds to move to given location
MOUSE_SPEED = 1

def get_screenshot():
    curr_time = time.strftime("%d %m %H%M%S", time.localtime())
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
    messages = [
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
    ]
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {OPENAI_KEY}"
    }
    payload = {
        "model": "gpt-4-vision-preview",
        "messages": messages,
        "max_tokens": 300
    }
    response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload)
    """
    response = openai.chat.completions.create(
        model="gpt-4-vision-preview",
        messages=messages
    )
    res = response.choices[0].message
    """
    res = response.json()['choices'][0]['message']['content']
    print("Screenshot description:")
    print(res)
    return res

def sem_sam(img):
    #img_link = "https://raw.githubusercontent.com/kcui5/vis/main/vispoetry/vispoetry/screens/08%2011%20013632.png"
    local_img = open(img, "rb")
    output = replicate.run(
        "cjwbw/semantic-segment-anything:b2691db53f2d96add0051a4a98e7a3861bd21bf5972031119d344d956d2f8256",
        input={"image": local_img}
    )
    print(output)
    return output

def owl_vit(img):
    img_link = "https://raw.githubusercontent.com/kcui5/vis/main/vispoetry/vispoetry/screens/08%2011%20013632.png"
    local_img = open(img, "rb")
    output = replicate.run(
        "alaradirik/owlvit-base-patch32:5e899f155a1913c4b7304d09082d842ca7fe6cb1f22e066c83eb1d7849dc37c2",
        input={
            "image": img_link,
            "query": "search bar"
        }
    )
    print(output)
    return output

def ram_grounded_sam(img):
    img_link = "https://raw.githubusercontent.com/kcui5/vis/main/vispoetry/vispoetry/screens/08%2011%20013632.png"
    local_img = open(img, "rb")
    output = replicate.run(
        "idea-research/ram-grounded-sam:80a2aede4cf8e3c9f26e96c308d45b23c350dd36f1c381de790715007f1ac0ad",
        input={
            "use_sam_hq": False,
            "input_image": img_link,
            "show_visualisation": True
        }
    )
    print(output)
    return output

def save_img_from_url(img_url):
    img_content = requests.get(img_url)

    if img_content.status_code == 200:
        curr_time = time.strftime("%d %m %H%M%S", time.localtime())
        path = os.getcwd() + f'/semsams/{curr_time}.png'
        with open(path, "wb") as file:
            file.write(img_content.content)
        return img_content.content
    else:
        print("Error retrieving image!")

def save_json_from_url(json_url):
    json_content = requests.get(json_url)
    if json_content.status_code == 200:
        curr_time = time.strftime("%d %m %H%M%S", time.localtime())
        path = os.getcwd() + f'/semsams/{curr_time}.json'
        with open(path, "w") as file:
            json.dump(json_content.json(), file, indent=4)
        return json_content.json()
    else:
        print("Error retrieving json!")

def try_get_coords_from_gpt(img, identify_obj):
    """Ask GPT-4V to estimate the pixel coordinates of the identify_obj in the image"""
    messages = [
        {
            "role": "user",
            "content": [
            {
                "type": "text",
                "text": f"Approximately what are the pixel coordinates of the {identify_obj} in the image? The origin of x=0, y=0 is at the top left of the screen. Increasing x goes to the right in the screen and increasing y goes down the screen. Respond only with the two integers representing an estimate of the pixel coordinates."
            },
            {
                "type": "image_url",
                "image_url": {
                    "url": f"data:image/jpeg;base64,{img}"
                }
            }
            ]
        }
    ]
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {OPENAI_KEY}"
    }
    payload = {
        "model": "gpt-4-vision-preview",
        "messages": messages,
        "max_tokens": 300
    }
    response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload)
    res = response.json()['choices'][0]['message']['content']
    print("Estimated pixel coordinates:")
    print(res)
    return res

def get_instructions(screenshot_description, task):
    """Get a list of the next three instructions for how to complete the task given the current state of the computer as a natural language description of the screenshot."""
    sys_msg = """Respond with the next three instructions for how to continue completing the given task given the current state of my computer. Respond in a numbered list of three simple and succinct instructions of how to continue completing the given task. The instructions should be basic computer inputs such as moving the mouse or hitting keys on the keyboard. Do not provide any unnecessary information such as alternative ways to complete the task, just provide each instruction precisely and succintly with each instruction as its own bullet point. For instructions involving clicking on the screen, separate the instruction into moving the mouse to the desired location and into left-clicking or right-clicking as separate bullet points. For instructions directing left-clicks, just only say 'left-click' without anything else."""

    user_prompt = f"The current state of my computer is as follows: {screenshot_description}. {task}"

    completion = openai.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": sys_msg},
            {"role": "user", "content": user_prompt}
        ]
    )

    instructions = completion.choices[0].message

    l = instructions.content.split("\n")
    print("Next three instructions for task: ")
    print(task)
    print(l)
    return l

def move_mouse(x, y):
    """Move the mouse to the given pixel coordinates"""
    print(f"Moving to {x} {y} + 50")
    pyautogui.moveTo(x, y + 50, MOUSE_SPEED)
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
    all_messages = []
    for instruct in instructions:
        messages = [
            {"role": "system", "content": "Provide instructions based on a generic macOS setup in a theoretical scenario."},
            {"role": "user", "content": instruct}
        ]
        all_messages.extend(messages)
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
                    "description": "Left-click the mouse. Used for any and all left-clicking.",
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
        all_messages.append(response_message)
        print(response_message)
        if tool_calls:
            available_functions = {
                "move_mouse": move_mouse,
                "mouse_click": mouse_click,
                "keyboard_type": keyboard_type
            }

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

                all_messages.append(
                    {
                        "tool_call_id": tool_call.id,
                        "role": "tool",
                        "function_to_call": function_to_call,
                        "function_args": function_args,
                    }
                )
    return all_messages

def pause(duration=1):
    print("Sleeping...")
    time.sleep(duration)

imgpath = os.getcwd() + '/screens/sunny desktop png.png'

sem_sam_output = sem_sam(imgpath)
sem_sam_img = sem_sam_output["img_out"]
sem_sam_json = sem_sam_output["json_out"]
save_img_from_url(sem_sam_img)
save_json_from_url(sem_sam_json)
"""
owl_vit_output = owl_vit(imgpath)
owl_vit_img = owl_vit_output["result_image"]
owl_vit_json = owl_vit_output["json_data"]
save_img_from_url(owl_vit_img)
save_json_from_url(owl_vit_json)

ram_grounded_sam_output = ram_grounded_sam(imgpath)
ram_grounded_sam_tags = ram_grounded_sam_output["tags"]
ram_grounded_sam_json = ram_grounded_sam_output["json_data"]
save_json_from_url(ram_grounded_sam_json)
"""

#image = encode_image(imgpath)
#try_get_coords_from_gpt(image, "search bar")
"""
task = "How can I go to amazon.com?"
task = input("What is my task?")

ss_path = get_screenshot()
base64_image = encode_image(ss_path)
vision_res = vision_screenshot(base64_image)
with open("log.txt", "w") as text_file:
    text_file.write(vision_res)
pause()


vision_res = ""
with open("log.txt", "r") as text_file:
    vision_res = text_file.read()

#print("Loaded vision_res:")
print(vision_res)


instructs = get_instructions(vision_res, task)
pause()

print("Setting up for auto commands")
pyautogui.moveTo(100, 100, 1)
pyautogui.click()

print(get_auto_commands(instructs))
"""