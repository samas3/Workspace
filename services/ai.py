import requests

class AI:
    def __init__(self, API_KEY, BASE_URL, system=None, model='gpt-4o-mini'):
        self.API_KEY = API_KEY
        self.BASE_URL = BASE_URL
        self.system = system
        self.messages = []
        self.model = model
        if system:
            self.init_system()
    
    def set_model(self, model):
        self.model = model
    
    def get_models(self):
        headers = {
            'Authorization': f'Bearer {self.API_KEY}',
            'Content-Type': 'application/json'
        }
        try:
            response = requests.get(f'{self.BASE_URL}/models', headers=headers)
            response.raise_for_status()
            data = response.json()
            models = [model['id'] for model in data['data']]
            return models
        except Exception as e:
            print(f"Error getting models: {e}")
            return []
    
    def init_system(self, max_tokens=2000, temperature=0.7):
        self.messages.append({'role': 'system', 'content': self.system})
        self._get_completion(max_tokens=max_tokens, temperature=temperature)
    
    def get_response(self, message):
        self.messages.append({'role': 'user', 'content': message})
        response_content = self._get_completion()
        if response_content:
            self.messages.append({'role': 'assistant', 'content': response_content})
            return response_content
        return None
    
    def _get_completion(self, max_tokens=2000, temperature=0.7):
        headers = {
            'Authorization': f'Bearer {self.API_KEY}',
            'Content-Type': 'application/json'
        }
        
        payload = {
            'model': self.model,
            'messages': self.messages,
            'temperature': temperature,
            'max_tokens': max_tokens
        }
        
        try:
            response = requests.post(
                f'{self.BASE_URL}/chat/completions',
                headers=headers,
                json=payload,
                timeout=30
            )
            response.raise_for_status()
            data = response.json()
            return data['choices'][0]['message']['content']
        except requests.exceptions.RequestException as e:
            print(f"Request error: {e}")
        except KeyError as e:
            print(f"Response format error: {e}")
        except Exception as e:
            print(f"Unexpected error: {e}")
        return None

if __name__ == '__main__':
    import voice
    API_KEY = 'sk-ChCzqxK2bcjznVVg3e571b93Dd9d4bE798631a7bB4770fFf'
    BASE_URL = 'https://one.aiskt.com/v1'
    system = '你是ChatGPT，一个由OpenAI训练的大语言模型。在你的回答中不能包含任何markdown字符，回答内容要尽量简短，不超过100字'
    ai = AI(API_KEY, BASE_URL, system, 'gpt-4o-mini')
    vr = voice.VoiceRecognition()
    tts = voice.TextToSpeech()
    res = vr.recognize('1.wav')
    if res:
        print(res)
        resp = ai.get_response(res)
        tts.speak(resp)