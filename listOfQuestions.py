import random
from askQuestion import speaksave
from callAIBackend import callChatAIforAnswer


def there_exists(terms,voice_data):
    for term in terms:
        if term in voice_data:
            return True
        

def respond(voice_data):
    # 1: greeting
    if there_exists(['hey','hi','hello'],voice_data):
        greetings = ["hey, how can I help you", "hey, what's up, how can I help you?", "I'm listening, how can I help you?", "Hi There, how can I help you?", f"hello Dear, how can I help you?"]
        greet = greetings[random.randint(0,len(greetings)-1)]
        speaksave(greet)
    
    # 2: greeting
    elif there_exists(["how are you","how are you doing"],voice_data):
        speaksave("I'm very well, thanks for asking ")
    
    # 3: no response
    elif there_exists(["noresponse"],voice_data):
        speaksave("I just noticed that you are quite from sometime. Do you need more time?")
    
    # 4: no response
    elif there_exists(["listeninbackground"],voice_data):
        speaksave("Looks like you need more time. I will be listening in background so please say hi when you are ready?")

    # 5: greeting
    elif there_exists(["exit", "quit", "goodbye","bye"],voice_data):
        speaksave("Thanks and have a good day.")

    else:
        speaksave("Sure, give me a moment and let me check that for you.")
        callChatAIforAnswer(voice_data)
