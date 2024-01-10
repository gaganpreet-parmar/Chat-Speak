import requests
from askQuestion import speaksave

def callChatAIforAnswer(question):
    url = 'http://localhost:9091/api/resource'
    credentials = ('username', 'password1')
    data = {
        'id': 1,
        'content': question,
    }
    print(f"question: {question}")
    response = requests.post(url, json=data, auth=credentials)
    answer = response.json()["message"]["result"]
    print(f"answer: {answer}")

    speaksave(answer)


