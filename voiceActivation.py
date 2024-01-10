import sounddevice as sd
import speech_recognition as sr
import time
import numpy as np
from cleanHumanVoice import clean_human_voice
from askQuestion import speaksave
from listOfQuestions import respond
import traceback

# Global variable
flag = False  
timeout_duration = 60  # seconds
reset_timeout_duration=60 # seconds
decrease_timeout_duration=10 # seconds
last_start_time = time.time()
humanNotResponsiveCount= 0
energy_threshold=500


def humanActive(value):
     global flag
     flag=value


def on_word_detected(recognizer, audio):
    # Create a speech recognition object
    #recognizer = sr.Recognizer()
    global flag,timeout_duration,last_start_time,humanNotResponsiveCount

    try:
        print("Listening...")

        # Apply energy-based VAD
        audio_int16 = np.frombuffer(audio.frame_data, dtype=np.int16)
        vad_segments = clean_human_voice(audio_int16, sample_rate=16000)

        if len(vad_segments) == 0:
            print("The audio is empty.")
            print(str(time.time() - last_start_time), " ", str(flag))
            if (time.time() - last_start_time > timeout_duration and flag):
                    print("User did not speak for last ",{timeout_duration},"sec. Ask if they need anything else")
                    if(humanNotResponsiveCount == 0):
                        respond("noresponse")
                    last_start_time = time.time()
                    humanNotResponsiveCount +=1
                    timeout_duration=timeout_duration-decrease_timeout_duration

                    if(humanNotResponsiveCount == 3):
                        print("Customer unresponsive and reset flag, also say to customer to say hi agian!! to restart")
                        respond("listeninbackground")
                        humanNotResponsiveCount=0
                        timeout_duration=reset_timeout_duration
                        flag=False
                        
        else:
            print("The audio is not empty.")
            # Recognize speech using Google Web Speech API
            text = recognizer.recognize_google(audio)
            
            print( text )

            if len(text)>0 :
                
                # Check if the keyword "hi C2" is present
                    last_start_time = time.time()
                    timeout_duration=reset_timeout_duration
                    flag=True
                    print("You said " + text.lower())
                    #speaksave("Hello, how are you.")
                    respond(text.lower())

    except sr.UnknownValueError:
        print("Could not understand audio.")

    except sr.RequestError as e:
        print(f"Error with the API request; {e}")


def listen_background():
    recognizer = sr.Recognizer()
    recognizer.energy_threshold = energy_threshold

    try:
        # Keep the program running while listening in the background
            with sr.Microphone() as source:
                print("Adjusting for ambient noise. Please remain silent.")
                recognizer.adjust_for_ambient_noise(source, duration=5)
                print("Ambient noise adjustment complete. You can start speaking.")

                while True:
                    #print("Started listening loop")
                    audio = recognizer.listen(source)
                    #print("Calling method")
                    on_word_detected(recognizer,audio)
                    time.sleep(1)
                    continue

    except KeyboardInterrupt:
        exit()

    except Exception as e:
        # Print a user-friendly message along with the exception details
        print("An error occurred:")
        print(f"Error Type: {type(e).__name__}")
        print(f"Error Details: {e}")
        
        # Print the traceback for more detailed information
        print("\nTraceback:")
        traceback.print_exc()

if __name__ == "__main__":
    listen_background()
