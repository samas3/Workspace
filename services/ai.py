from openai import OpenAI
class AI:
    def __init__(self, API_KEY, BASE_URL, system=None, model='gpt-4o-mini'):
        self.API_KEY = API_KEY
        self.BASE_URL = BASE_URL
        self.system = system
        self.messages = []
        self.ai = OpenAI(api_key=API_KEY, base_url=BASE_URL)
        self.model = model
        if system:
            self.init_system()
    def set_model(self, model):
        self.model = model
    def get_models(self):
        response = self.client.models.list()
        models = [model.id for model in response.data]
        return models
    def init_system(self, max_tokens=2000, temperature=0.7):
        self.messages.append({'role': 'system', 'content': self.system})
        try:
            res = self.ai.chat.completions.create(model=self.model, messages=self.messages, temperature=temperature, max_tokens=max_tokens)
        except Exception as e:
            print(e)
    def get_response(self, message):
        self.messages.append({'role': 'user', 'content': message})
        try:
            res = self.ai.chat.completions.create(model=self.model, messages=self.messages, temperature=0.7, max_tokens=2000)
        except Exception as e:
            print(e)
        else:
            self.messages.append(res.choices[0].message.content)
            return res.choices[0].message.content

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