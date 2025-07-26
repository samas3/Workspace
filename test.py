from utils import util
from services import voice
import yaml
with open('config/settings.yaml', 'r') as file:
    config = yaml.safe_load(file)
# recognition = voice.VoiceRecognition(config['voice']['API_KEY'])
util.set_volume(100)
util.record(48000, 5, "media/test_mic.wav")
util.set_volume(100)
util.play_audio("media/test_mic.wav")
# print(recognition.recognize("media/test_mic.wav"))
# voice.TextToSpeech().speak("你说得对")
# util.play_audio("media/output.wav")