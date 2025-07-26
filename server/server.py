from flask import Flask, render_template, request, jsonify
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from core import ai_conversation
from utils import util
from services import voice
from hardware import motor_control
motor = motor_control.MotorController()
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
        print(resp)
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
@app.route('/move_forward', methods=['POST'])
def move_forward():
    """前进"""
    try:
        motor.forward(5)
        return jsonify({'status': 'success', 'message': '前进'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})
@app.route('/move_backward', methods=['POST'])
def move_backward():
    """后退"""
    try:
        motor.backward(5)
        return jsonify({'status': 'success', 'message': '后退'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})
@app.route('/turn_left', methods=['POST'])
def turn_left():
    """左转"""
    try:
        motor.left(0.3)
        return jsonify({'status': 'success', 'message': '左转'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})
@app.route('/turn_right', methods=['POST'])
def turn_right():
    """右转"""
    try:
        motor.right(0.3)
        return jsonify({'status': 'success', 'message': '右转'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})
def main():
    """主函数"""
    try:
        app.run(debug=True, host='10.31.2.131', port=5000)
    except Exception as e:
        print(f"❌ 服务器启动失败: {e}")
if __name__ == '__main__':
    main()