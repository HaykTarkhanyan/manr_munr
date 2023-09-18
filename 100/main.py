import streamlit as st
import pandas as pd
import plotly.express as px
import openai
import time
import os
import re
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

class Text(BaseModel):
    text: str

prompt = {"role": "system", "content": """
    You are IconMaster, a visual design assistant. 
    I will provide you with a text and you will return the shortcode of icon(like :smile:) that
    best fits the given text. 
    
    You should only reply with the icon code, not any other text. don;t tell anything else.
    
    dont use html/css or any other code. just the shortcode of the icon.
    
    Examples:
    Text: "A family of 4 is going to the beach."
    Response: ":family:"
    
    Text: "Banking system, financial services, money transfer."
    Response: ":bank:"
    """
}


openai.api_key = os.environ['OPENAI_API_KEY']

@st.cache(allow_output_mutation=True)
def get_input_list():
    return []

history = get_input_list()

# def show_progress_bar(delay: int) -> None:
#     progress_bar = st.progress(0)
#     for i in range(100):
#         time.sleep(delay / 100)
#         progress_bar.progress(i + 1)



def request_plotly_code(history) -> str:
    messages = [
                prompt,
                ]
    if history:
        messages.extend(history)

    st.write("History:")
    st.code(messages)
    response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=messages)
                   

    return response['choices'][0]['message']['content'].strip()

@app.post("/get_icon")
async def get_icon(text: Text):
    history.append({"role": "user", "content": text.text})
    
    response = request_plotly_code(history)
    only_icon = re.findall(r':(.*?):', response)
    only_icon = [f":{icon}:" for icon in only_icon]
    history.append({"role": "assistant", "content": response})
    
    
    # del history[-2:]
    return {"icon": only_icon}

st.title("Hundread FinCopilot Icon Classifier")

# have_history = st.checkbox("Have history", value=False)

text = st.text_input("Provide the text")
print(f"Time {time.localtime()}")
print(f"Prompt: {prompt}")


print(f"\n \nHisory {history}")
history.append({"role": "user", "content": text})


response = request_plotly_code(history)


only_icon = re.findall(r':(.*?):', response)
print(only_icon)
only_icon = [f":{icon}:" for icon in only_icon]


st.write(f"Response: {response}")
st.write(f"Icon: {only_icon}")

history.append({"role": "assistant", "content": response})

# if not have_history:
#     del history[-2:]
