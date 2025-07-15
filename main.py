import os
import asyncio
import requests
from dotenv import load_dotenv
import streamlit as st
from data import rishtas
from agents import AsyncOpenAI, OpenAIChatCompletionsModel, RunConfig, Agent, Runner, function_tool
load_dotenv()
api = os.getenv("OPENAI_KEY")
token = os.getenv("TOKEN")

st.title("Rishta Wali Aunty 📱💌")

name = st.text_input("Enter your name")
age = st.number_input("Enter your age", min_value=18, max_value=100)
gender = st.selectbox("Select your gender", ["Male", "Female"])
profession = st.text_input("Enter your profession")
education = st.text_input("Enter your education")
number = st.text_input("Enter your WhatsApp number (without +92)")
message = st.text_area("Write your own intro or message")

number = number.replace(" ", "").replace("-", "")
message = message.replace("\n", " ")

user_data = {
    "name": name,
    "age": age,
    "gender": gender,
    "profession": profession,
    "education": education,
    "number": number,
    "message": message
}



@function_tool
def send_whatsapp_message():
    url = f"https://api.ultramsg.com/instance131802/messages/chat"
    payload = {
        "token": token,
        "to": f"+92{user_data['number']}",
        "body": user_data['message']
    }
    res = requests.post(url, data=payload)
    print("Message response:", res.text)

external_agent = AsyncOpenAI(api_key=api,base_url="https://generativelanguage.googleapis.com/v1beta/openai/")
model = OpenAIChatCompletionsModel(openai_client=external_agent, model="gemini-2.0-flash")

config = RunConfig(
    model=model,
    model_provider=external_agent,
    tracing_disabled=True
)

agent = Agent(
    name="Rishta_Wali_Aunty",
   instructions="""
You are Rishta Wali Aunty. Your job is to find a perfect match from the rishta list based on the user's gender.
If the user is Male, suggest a Female match from the list and vice versa.
Suggest only one perfect rishta and explain why it's a good match.

After choosing the match, you MUST call the tool send_whatsapp_message() to send the rishta details to the user's WhatsApp.
Always confirm you used the tool.
""",
    tools=[send_whatsapp_message],
)

async def main():
    opposite_gender = "Female" if user_data["gender"] == "Male" else "Male"
    match = next((r for r in rishtas if r["gender"] == opposite_gender), None)

    match_info = (
        f"Name: {match['name']}\n"
        f"Age: {match['age']}\n"
        f"Profession: {match['profession']}\n"
        f"Education: {match['education']}"
    ) if match else "No suitable match found."

    full_prompt = (
    f"My name is {name}, I am a {age} year old {gender}. "
    f"I work as a {profession} and my education is {education}. "
    f"Please find a rishta for me based on opposite gender, and then send this to my WhatsApp using your tool."
    )


    user_data["message"] = f"Rishta suggestion:\n{match_info}"
    result = await Runner.run(agent, full_prompt, run_config=config)
    return result.final_output

if st.button("Find My Rishta & Send on WhatsApp"):
    if not api or not token:
        st.error("API Key or Token missing.")
    elif not number or not message:
        st.warning("Please fill in number and message.")
    else:
        output = asyncio.run(main())
        st.success("Message sent to WhatsApp successfully!")
        st.write("Agent Reasoning:", output)
        st.write("Your Provided Info:", user_data)
