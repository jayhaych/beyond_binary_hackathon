import speech_recognition as sr

def list_microphones():
    print("🔍 SCANNING AUDIO DEVICES...")
    mics = sr.Microphone.list_microphone_names()
    
    if not mics:
        print("❌ ERROR: No microphones found on this computer!")
        return

    print(f"✅ Found {len(mics)} devices:")
    for i, name in enumerate(mics):
        print(f"   [Index {i}] {name}")

    print("\n" + "="*40)
    
    # Ask user to pick one to test
    try:
        choice = int(input("👉 Enter the INDEX number of your headset/mic to test: "))
    except ValueError:
        print("Invalid number.")
        return

    print(f"\n🎧 Testing Device Index {choice}...")
    recognizer = sr.Recognizer()
    
    try:
        # FORCE select the chosen microphone
        with sr.Microphone(device_index=choice) as source:
            print("🎤 PLEASE SPEAK NOW (Say 'Hello')...")
            # Using a very short duration to fail fast if it's dead
            recognizer.adjust_for_ambient_noise(source, duration=1)
            audio = recognizer.listen(source, timeout=5)
            print("✅ Audio captured! Processing...")
            
            text = recognizer.recognize_google(audio)
            print(f"🎉 SUCCESS! Heard: '{text}'")
            print(f"\n💡 FIX: Update your code to use `sr.Microphone(device_index={choice})`")
            
    except sr.WaitTimeoutError:
        print("❌ TIMEOUT: This microphone heard nothing. Try a different index.")
    except Exception as e:
        print(f"❌ ERROR: {e}")

if __name__ == "__main__":
    list_microphones()