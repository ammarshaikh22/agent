import os
import asyncio
import requests
from dotenv import load_dotenv
import streamlit as st
from data import rishtas
from agents import AsyncOpenAI, OpenAIChatCompletionsModel, RunConfig, Agent, Runner, function_tool

# Load environment variables
load_dotenv()
api = os.getenv("OPENAI_KEY")
token = os.getenv("TOKEN")

# Streamlit UI
st.title("Rishta Wali Aunty 📱💌")

name = st.text_input("Enter your name")
age = st.number_input("Enter your age", min_value=18, max_value=100)
gender = st.selectbox("Select your gender", ["Male", "Female"])
profession = st.text_input("Enter your profession")
education = st.text_input("Enter your education")
number = st.text_input("Enter your WhatsApp number (without +92)")
message = st.text_area("Write your own intro or message (optional)")

# Clean inputs
number = number.replace(" ", "").replace("-", "")
message = message.replace("\n", " ")

# User data
user_data = {
    "name": name,
    "age": age,
    "gender": gender,
    "profession": profession,
    "education": education,
    "number": number,
    "message": message
}

# WhatsApp tool
@function_tool
def send_whatsapp_message():
    url = "https://api.ultramsg.com/instance132485/messages/chat"
    payload = {
        "token": token,
        "to": f"+92{user_data['number']}",
        "body": user_data["message"]
    }
    res = requests.post(url, data=payload)
    print("Message response:", res.text)

# Agent setup
external_agent = AsyncOpenAI(
    api_key=api,
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/"
)

model = OpenAIChatCompletionsModel(
    openai_client=external_agent,
    model="gemini-2.0-flash"
)

config = RunConfig(
    model=model,
    model_provider=external_agent,
    tracing_disabled=True
)

agent = Agent(
    name="Rishta_Wali_Aunty",
    instructions="""
You are Rishta Wali Aunty 🤝 — your task is to find a perfect rishta from the provided list based on user's *opposite gender*.

Only return ONE best match, and explain briefly why it's a suitable rishta. After that, you MUST send a WhatsApp message using the `send_whatsapp_message()` tool.

⚠️ IMPORTANT:
- The message you send *must include both* the user's details and the rishta's details in a clear format.
- Do NOT change the content of the message given in the prompt — just pass it to the tool.
- Always confirm after using the tool that the message was sent.
""",
    tools=[send_whatsapp_message],
)

# Matching logic + agent runner
async def main():
    opposite_gender = "Female" if user_data["gender"] == "Male" else "Male"

    def score_match(rishta):
        age_diff = abs(rishta["age"] - user_data["age"])
        profession_match = 0 if rishta["profession"].lower() == user_data["profession"].lower() else 5
        return age_diff + profession_match

    eligible_matches = [r for r in rishtas if r["gender"] == opposite_gender]
    match = min(eligible_matches, key=score_match, default=None)

    if match:
        match_info = (
            f"🌟 *Match Found!*\n"
            f"👤 Name: {match['name']}\n"
            f"🎂 Age: {match['age']}\n"
            f"💼 Profession: {match['profession']}\n"
            f"🎓 Education: {match['education']}"
        )
    else:
        match_info = "❌ No suitable match found."

    # WhatsApp message to be sent
    full_message = (
        f"📋 *Your Info:*\n"
        f"Name: {user_data['name']}\n"
        f"Age: {user_data['age']}\n"
        f"Gender: {user_data['gender']}\n"
        f"Profession: {user_data['profession']}\n"
        f"Education: {user_data['education']}\n\n"
        f"{match_info}"
    )

    # Save message to global user_data for the tool to use
    user_data["message"] = full_message

    prompt = (
        f"Please send the following message on WhatsApp using the tool:\n\n{full_message}"
    )

    result = await Runner.run(agent, prompt, run_config=config)
    return full_message, result.final_output

# Streamlit button and execution
if st.button("Find My Rishta & Send on WhatsApp"):
    if not api or not token:
        st.error("API Key or Token missing.")
    elif not number:
        st.warning("Please enter your WhatsApp number.")
    else:
        final_message, reasoning = asyncio.run(main())
        st.success("✅ Message sent to WhatsApp successfully!")
        st.markdown("### 📤 Message Sent:")
        st.code(final_message)
        st.markdown("### 🧠 Agent Reasoning:")
        st.write(reasoning)
        st.markdown("### 📝 Your Input Info:")
        st.json(user_data)
