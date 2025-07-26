import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from dashscope.audio.tts import SpeechSynthesizer
import yaml
from http import HTTPStatus
from dashscope.audio.asr import Recognition
import dashscope
class TextToSpeech:
    """文本转语音服务类"""
    
    def __init__(self):
        """初始化文本转语音服务
        """
        with open('config/settings.yaml', 'r') as f:
            dashscope.api_key = yaml.safe_load(f)['voice']['API_KEY']

    def speak(self, text, model='sambert-zhichu-v1', output='media/output.wav'):
        """将文本转换为语音并播放
        
        Args:
            text: 要转换的文本
        """
        if not text:
            print("Error: No text provided for speech synthesis.")
            return
        result = SpeechSynthesizer.call(model=model,
                                        text=text,
                                        sample_rate=48000,
                                        format='wav')
        if result.get_audio_data() is not None:
            with open(output, 'wb') as f:
                f.write(result.get_audio_data())
        else:
            print('ERROR: response is %s' % (result.get_response()))
class VoiceRecognition:
    """语音识别服务类"""
    
    def __init__(self):
        """初始化语音识别服务
        """
        with open('config/settings.yaml', 'r') as f:
            dashscope.api_key = yaml.safe_load(f)['voice']['API_KEY']
        self.recognition = Recognition(model='paraformer-realtime-v2',
                                format='wav',
                                sample_rate=16000,
                                # “language_hints”只支持paraformer-realtime-v2模型
                                language_hints=['zh', 'en'],
                                callback=None)

    def recognize(self, audio_file='media/test_mic.wav'):
        """识别音频文件中的语音
        """
        if not os.path.exists(audio_file):
            print(f"Error: Audio file {audio_file} does not exist.")
            return None
        result = self.recognition.call(audio_file)
        if result.status_code == HTTPStatus.OK:
            sentences = result.get_sentence()
            if not sentences:
                print('No speech detected.')
                return None
            res = ''.join([i['text'] for i in sentences])
            print(res)
            return res
        else:
            print('Error: ', result.message)
            return None