import pyttsx3
from dashscope.audio.asr import *

class VoiceRecognition:
    def __init__(self):
        self.recognizer = sr.Recognizer()
    def get_text(self):
        with sr.Microphone() as source:
            self.recognizer.adjust_for_ambient_noise(source)
            audio = self.recognizer.listen(source)
        try:
            #txt = self.recognizer.recognize_sphinx(audio, language='zh-CN')
            txt = self.recognizer.recognize_google(audio, language='zh-CN')
            print(txt)
        except Exception as e:
            print(e)

class TextToSpeech:
    def __init__(self):
        self.engine = pyttsx3.init()
    def speak(self, text, rate=113):
        self.engine.setProperty('rate', rate)
        self.engine.say(text)
        self.engine.runAndWait()
while 1:
    VoiceRecognition().get_text()