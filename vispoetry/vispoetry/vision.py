import os
import time
import requests
import pyautogui
import openai
import base64

OPENAI_KEY = 

curr_time = time.strftime("%H%M%S", time.localtime())
path = os.getcwd() + f'/screens/{curr_time}.png'
ss = pyautogui.screenshot()
ss.save(path)

def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')
    
base64_image = encode_image(path)

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
              "url": f"data:image/jpeg;base64,{base64_image}"
            }
          }
        ]
      }
    ],
    "max_tokens": 300
}

response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload)

res = response.json()['choices'][0]['message']['content']

with open("log.txt", "w") as text_file:
    text_file.write(res)

print(f"Taking screenshot at {path}")
print("Screenshot description:")
print(res)

sys_msg = "Respond in a numbered list of simple and succinct instructions of how to complete the given task. The instructions should be basic computer inputs such as moving the mouse or hitting keys on the keyboard. Do not provide any unnecessary information such as alternative ways to complete the task, just provide each instruction precisely and succintly with each instruction as its own bullet point. For instructions involving clicking on the screen, separate the instruction into moving the mouse to the desired location and into left-clicking or right-clicking as separate bullet points."

task = f"The current state of my computer is as follows: {res}. How can I go to amazon.com?"

completion = openai.ChatCompletion.create(
  model="gpt-4",
  messages=[
    {"role": "system", "content": sys_msg},
    {"role": "user", "content": task}
  ]
)

res = completion.choices[0].message

print("Instructions for task: ")
print(task)
print(res)

l = res["content"].split("\n")

pyautogui.FAILSAFE = True

#Number of seconds to move to given location
MOUSE_SPEED = 1

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

def type(word):
    """Type the given word"""
    print(f"Typing: {word}")
    pyautogui.typewrite(word)
    return

def run_conversation():
    messages = [{"role": "user", "content": l[0]}]
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
                "description": "Left click the mouse."
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
                "name": "type",
                "description": "Types the given string of characters on the keyboard."
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
    
    if tool_calls:
        # Step 3: call the function
        # Note: the JSON response may not always be valid; be sure to handle errors
        available_functions = {
            "move_mouse": move_mouse,
        }  # only one function in this example, but you can have multiple
        messages.append(response_message)  # extend conversation with assistant's reply
        # Step 4: send the info for each function call and function response to the model
        for tool_call in tool_calls:
            function_name = tool_call.function.name
            function_to_call = available_functions[function_name]
            function_args = json.loads(tool_call.function.arguments)
            function_response = function_to_call(
                x=function_args.get("x"),
                y=function_args.get("y"),
            )
            messages.append(
                {
                    "tool_call_id": tool_call.id,
                    "role": "tool",
                    "name": function_name,
                    "content": function_response,
                }
            )  # extend conversation with function response
        """second_response = openai.chat.completions.create(
            model="gpt-3.5-turbo-1106",
            messages=messages,
        )  # get a new response from the model where it can see the function response"""
        return messages
print(run_conversation())