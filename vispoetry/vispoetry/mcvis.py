import pyautogui
from openai import OpenAI
import base64
import time

#GPT-4V screenshot of Minecraft screen goes to state description. GPT-4 cascades
#tiers of decomposing tasks eventually into atomic instructions.
#GPT-4 self-prompts at each level

#GPT-4V screenshot of Minecraft screen to ask for next step.

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

client = OpenAI()

pyautogui.FAILSAFE = True
#Number of seconds to move to given location
MOUSE_SPEED = 1

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
    
def ask_gpt_4v(img, messages):
    """Get the GPT-4V response describing what is in the given screenshot image"""
    
    completion = client.chat.completions.create(
        model="gpt-4-vision-preview",
        messages=messages
    )
    res = completion.choices[0].message
    
    return res



def main():
    ss_path = get_screenshot()
    encoded_img = encode_image(ss_path)

if __name__ == "__main__":
    main()