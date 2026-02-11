import time
import pyttsx3
import speech_recognition as sr

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

# --- 2. MICROPHONE LOGIC (With "Fuzzy" Matching) ---
def listen_for_answer():
    recognizer = sr.Recognizer()
    
    # USE YOUR WORKING DEVICE INDEX (1)
    try:
        with sr.Microphone(device_index=1) as source:
            print("\n🎤 LISTENING... (Tip: Say 'Option A' or 'Alpha' for better accuracy)")
            
            # Fast adjust
            recognizer.adjust_for_ambient_noise(source, duration=0.5)
            # High sensitivity
            recognizer.energy_threshold = 300  
            
            try:
                # Listen
                audio = recognizer.listen(source, timeout=10)
                print("   Processing...")
                
                # Convert to text
                text = recognizer.recognize_google(audio).upper()
                print(f"✅ I HEARD: '{text}'")
                
                # --- MAGICAL "FUZZY" MATCHING ---
                # We check for words that SOUND like the letters
                
                # Check for A
                if any(x in text for x in ["A", "HEY", "AY", "EIGHT", "ALPHA", "OPTION A", "EH"]): 
                    return "A"
                
                # Check for B
                if any(x in text for x in ["B", "BEE", "BE", "ME", "BRAVO", "OPTION B"]): 
                    return "B"
                
                # Check for C
                if any(x in text for x in ["C", "SEA", "SEE", "SI", "SHE", "CHARLIE", "OPTION C"]): 
                    return "C"
                
                # Check for D
                if any(x in text for x in ["D", "DEE", "THE", "DAY", "DELTA", "OPTION D"]): 
                    return "D"
                
                return None

            except sr.WaitTimeoutError:
                print("❌ TIMEOUT: Silence.")
                return None
            except sr.UnknownValueError:
                print("❌ UNINTELLIGIBLE.")
                return None
            except Exception as e:
                print(f"❌ ERROR: {e}")
                return None
    except OSError:
        print("❌ CRITICAL: Mic Index 1 not found.")
        return None

# --- 3. GAME LOOP ---
def run_game():
    # HARDCODED DATA
    quiz_data = [
        {
            "q": "What is 2 plus 2?",
            "options": ["Three", "Four", "Five", "Six"],
            "correct": "B" 
        },
        {
            "q": "Which is a fruit?",
            "options": ["Carrot", "Steak", "Apple", "Bread"],
            "correct": "C"
        }
    ]

    print("="*40)
    print("STARTING VOICE QUIZ")
    print("="*40)

    speak("Voice Quiz Started. PRO TIP: Say 'Option A' or 'Alpha' to be heard clearly.")
    time.sleep(0.5)

    score = 0

    for i, item in enumerate(quiz_data):
        print(f"\n--- Question {i+1} ---")
        
        # Read Question
        speak(f"Question {i+1}: {item['q']}")
        time.sleep(0.5)
        
        # Read Options
        speak(f"A: {item['options'][0]}")
        speak(f"B: {item['options'][1]}")
        speak(f"C: {item['options'][2]}")
        speak(f"D: {item['options'][3]}")
        
        # Listen Loop
        user_choice = None
        while not user_choice:
            user_choice = listen_for_answer()
            if not user_choice:
                speak("I didn't catch that. Please say 'Option A' or 'Alpha'.")
        
        # Grade
        if user_choice == item['correct']:
            speak("Correct!")
            score += 1
        else:
            speak(f"Incorrect. The answer was {item['correct']}.")
        
        time.sleep(1)

    speak(f"Quiz complete. You got {score} out of {len(quiz_data)}.")

if __name__ == "__main__":
    run_game()