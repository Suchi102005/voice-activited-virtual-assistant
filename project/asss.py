# assistant.py
import os
import openai
import speech_recognition as sr
import pyttsx3
import datetime
import requests
import spacy
import pytz
import sys
import threading
from dotenv import load_dotenv
from colorama import Fore, Style, init
from mic_gui import VoiceVisualizer
from PyQt5.QtWidgets import QApplication

# Init
init(autoreset=True)
load_dotenv()
openai.api_key = os.getenv("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")
WEATHER_API_KEY = os.getenv("3eb860411d4177830270e27ec51063cb")

# Engines
engine = pyttsx3.init()
recognizer = sr.Recognizer()
nlp = spacy.load("en_core_web_sm")

WAKE_WORD = "jarvis"
CITY = "Chennai"


# Assistant features
def speak(text):
    print(f"{Fore.MAGENTA}🤖 Assistant:{Style.RESET_ALL} {text}")
    engine.say(text)
    engine.runAndWait()

def listen(timeout=5):
    with sr.Microphone() as source:
        print(f"{Fore.GREEN}🔊 Listening...{Style.RESET_ALL}")
        try:
            audio = recognizer.listen(source, timeout=timeout)
            text = recognizer.recognize_google(audio)
            print(f"{Fore.BLUE}👤 You said:{Style.RESET_ALL} {text}")
            return text.lower()
        except Exception as e:
            print(f"{Fore.RED}Error:{Style.RESET_ALL} {e}")
            return None

def get_current_time():
    tz = pytz.timezone('Asia/Kolkata')
    return datetime.datetime.now(tz).strftime("%I:%M %p")

def get_current_date():
    return datetime.datetime.now().strftime("%A, %B %d, %Y")

def get_weather(city=CITY):
    try:
        base_url = "http://api.openweathermap.org/data/2.5/weather"
        params = {'q': city, 'appid': WEATHER_API_KEY, 'units': 'metric'}
        response = requests.get(base_url, params=params)
        data = response.json()
        if response.status_code == 200:
            temp = data['main']['temp']
            desc = data['weather'][0]['description']
            return f"The weather in {city} is {desc} with {temp}°C"
        else:
            return "Sorry, I couldn't fetch the weather."
    except Exception as e:
        return "Weather service is unavailable."

def detect_intent(text):
    text = text.lower()
    doc = nlp(text)
    if any(word in text for word in ['time', 'clock']):
        return "time_query"
    elif any(word in text for word in ['date', 'today']):
        return "date_query"
    elif 'weather' in text:
        return "weather_query"
    elif any(w in text for w in ['joke', 'funny']):
        return "entertainment"
    return "general"

def chat_with_gpt(prompt):
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=150
        )
        return response.choices[0].message.content
    except Exception as e:
        return "AI service is down."

def process_command(command):
    intent = detect_intent(command)
    if intent == "time_query":
        return get_current_time()
    elif intent == "date_query":
        return get_current_date()
    elif intent == "weather_query":
        return get_weather()
    elif intent == "entertainment":
        return "Why did the computer show up late? It had a hard drive!"
    return None

# Main loop
def main():
    print(f"{Fore.CYAN}🎙️ Assistant Running — Say '{WAKE_WORD}' to activate.{Style.RESET_ALL}")
    while True:
        user_input = listen()
        if not user_input:
            continue

        if WAKE_WORD in user_input:
            speak("How can I help you?")
            command = listen(timeout=8)
            if not command:
                continue

            local_reply = process_command(command)
            if local_reply:
                speak(local_reply)
            else:
                speak(chat_with_gpt(command))

        elif "exit" in user_input or "stop" in user_input:
            speak("Goodbye!")
            break

if __name__ == "__main__":

    main()
