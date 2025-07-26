from flask import Flask, render_template, request, jsonify
import json
import time
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from core import ai_conversation
from utils import util
from services import voice
app = Flask(__name__)
ai = ai_conversation.AIConversation()
tts = voice.TextToSpeech()
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/process_text', methods=['POST'])
def process_text():
    """处理识别后的文本"""
    try:
        data = request.get_json()
        text = data.get('text', '')
        if not text:
            return jsonify({'status': 'error', 'message': '文本为空'})
        resp = ai.process_input(text)
        tts.speak(resp)
        util.set_volume(100)
        util.play_audio('media/output.wav')
        # print(resp)
        return jsonify({
            'status': 'success',
            'processed_result': text,
            'result': resp
        })
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'处理失败: {str(e)}'
        })

if __name__ == '__main__':
    app.run(debug=True, host='10.31.2.131', port=5000)