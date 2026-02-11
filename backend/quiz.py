import json
import time
import re
import os
import google.generativeai as genai
import pyttsx3
import speech_recognition as sr
import dotenv

dotenv.load_dotenv() 

# --- 1. TTS SETUP ---
def speak(text):
    print(f"🗣️ AI: {text}")
    try:
        engine = pyttsx3.init()
        engine.setProperty('rate', 160)
        engine.say(text)
        engine.runAndWait()
    except Exception as e:
        print(f"TTS Error: {e}")

# --- 2. MICROPHONE SETUP (Your Working Settings) ---
def listen_for_answer():
    recognizer = sr.Recognizer()
    try:
        # USE DEVICE INDEX 1 (Verified Working)
        with sr.Microphone(device_index=1) as source:
            print("\n🎤 LISTENING... (Say 'Option A' or 'Alpha')")
            
            recognizer.adjust_for_ambient_noise(source, duration=0.5)
            recognizer.energy_threshold = 300  # Force sensitivity
            
            try:
                audio = recognizer.listen(source, timeout=10)
                text = recognizer.recognize_google(audio).upper()
                print(f"✅ I HEARD: '{text}'")
                
                # Fuzzy Match Letters
                if any(x in text for x in ["A", "HEY", "EI", "OPTION A", "ALPHA"]): return "A"
                if any(x in text for x in ["B", "BEE", "BE", "OPTION B", "BRAVO"]): return "B"
                if any(x in text for x in ["C", "SEA", "SEE", "SI", "OPTION C"]): return "C"
                if any(x in text for x in ["D", "DEE", "THE", "OPTION D"]): return "D"
                return None

            except sr.WaitTimeoutError:
                return None
            except sr.UnknownValueError:
                return None
            except Exception as e:
                print(f"Error: {e}")
                return None
    except OSError:
        print("❌ CRITICAL: Mic Index 1 not found.")
        return None

# --- 3. QUIZ CLASS ---
class VoiceQuiz:
    def __init__(self, gemini_api_key):
        genai.configure(api_key=gemini_api_key)
        self.model = genai.GenerativeModel('gemini-2.5-flash')

    def generate(self, text_content):
        """Generates REAL questions from the PDF text"""
        print("🧠 Generating quiz from notes...")
        prompt = f"""
        Create a 3-question multiple choice quiz based on these notes.
        Format purely as JSON.
        Structure:
        {{
            "questions": [
                {{
                    "q": "Question text?",
                    "options": ["Option A", "Option B", "Option C", "Option D"],
                    "correct": "A" 
                }}
            ]
        }}
        Notes: {text_content[:2000]}
        """
        try:
            response = self.model.generate_content(prompt)
            clean_json = response.text.replace("```json", "").replace("```", "").strip()
            return json.loads(clean_json)
        except Exception as e:
            print(f"Gemini Error: {e}")
            return None

    def start_interactive_session(self, text_content):
        """Runs the Voice Quiz Loop and RETURNS the results."""
        
        # 1. Generate Questions
        quiz_data = self.generate(text_content)
        
        if not quiz_data:
            speak("Sorry, I could not generate a quiz.")
            return None

        score = 0
        total = len(quiz_data['questions'])
        
        speak("I have generated a quiz based on your notes. Say Option A, B, C, or D.")
        time.sleep(0.5)

        # 2. Loop Through Questions
        for i, item in enumerate(quiz_data['questions']):
            # Read Question
            speak(f"Question {i+1}: {item['q']}")
            time.sleep(0.3)
            
            # Clean and Read Options
            letters = ["A", "B", "C", "D"]
            for idx, opt_text in enumerate(item['options']):
                letter = letters[idx]
                # Remove "A)", "Option A" etc for cleaner speech
                clean_text = re.sub(r"^(Option\s)?[A-D][\)\.:-]\s*", "", opt_text, flags=re.IGNORECASE)
                speak(f"Option {letter}: {clean_text}")
                time.sleep(0.2)
            
            # Listen for Answer
            user_choice = None
            attempts = 0
            while not user_choice and attempts < 2:
                user_choice = listen_for_answer()
                if not user_choice:
                    if attempts == 0: speak("I didn't catch that.")
                    attempts += 1
            
            # Check Result
            if not user_choice:
                speak(f"Moving on. The answer was {item['correct']}.")
            elif user_choice == item['correct']:
                speak("Correct!")
                score += 1
            else:
                speak(f"Incorrect. The answer was {item['correct']}.")
            
            time.sleep(0.5)

        speak(f"Quiz complete. You got {score} out of {total}. Check your screen for the summary.")
        
        # [NEW] Return the results so Frontend can display them
        return {
            "score": score,
            "total": total,
            "questions": quiz_data['questions']
        }

# Wrapper function for main.py to call
def run_quiz_from_text(text):
    key = os.getenv("GEMINI_API_KEY")
    bot = VoiceQuiz(key)
    return bot.start_interactive_session(text)