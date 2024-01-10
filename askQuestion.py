from gtts import gTTS
from io import BytesIO
import time
import pygame


def text_to_speech(text, language='en'):
    # Create a gTTS object
    tts = gTTS(text=text, lang=language, slow=False)

    # Convert gTTS to audio data
    audio_data = BytesIO()
    tts.write_to_fp(audio_data)   
    return audio_data

def askQuestion(text):
    pygame.init()
    pygame.mixer.init()
    #text = "Hello, how are you. How can i help you today."
    audio_data= text_to_speech(text)

    # Play the audio
    audio_data.seek(0)
    sound = pygame.mixer.Sound(audio_data)
    sound.play()

    while pygame.mixer.get_busy():
        time.sleep(0.1)

    pygame.mixer.quit()
    pygame.quit()

def speaksave(text, language='en'):
    pygame.init()
    pygame.mixer.init()
    tts = gTTS(text, lang=language, slow=False)
    tts.save("myfile.mp3")
    sound = pygame.mixer.Sound("myfile.mp3")
    sound.play()
    while pygame.mixer.get_busy():
        time.sleep(1)

    pygame.mixer.quit()
    pygame.quit()


#speaksave("Python is cool always")
