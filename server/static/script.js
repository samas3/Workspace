const $ = (i) => document.getElementById(i);

class VoiceRecognitionApp {
    constructor() {
        this.isRecording = false;
        this.mediaRecorder = null;
        this.audioChunks = [];
        this.recognition = null;
        this.finalTranscript = '';
        
        this.recordButton = document.getElementById('record-btn');
        this.statusElement = document.getElementById('status');
        this.loadingElement = document.getElementById('loading');
        this.resultElement = document.getElementById('result');
        this.errorMessage = document.getElementById('error-message');
        this.recognizedText = document.getElementById('recognized-text');
        this.textContent = document.getElementById('text-content');
        this.permissionInfo = document.getElementById('permission-info');
        
        this.init();
    }
    
    init() {
        this.recordButton.addEventListener('click', () => {
            this.toggleRecording();
        });
        
        // 检查浏览器支持
        if (!('webkitSpeechRecognition' in window) && !('SpeechRecognition' in window)) {
            this.showError('您的浏览器不支持语音识别功能，请使用Chrome浏览器');
            this.recordButton.disabled = true;
        }
    }
    
    async toggleRecording() {
        if (this.isRecording) {
            this.stopRecording();
        } else {
            await this.startRecording();
        }
    }
    
    async startRecording() {
        try {
            this.hideError();
            this.hideResult();
            this.hideRecognizedText();
            
            // 初始化语音识别
            this.initSpeechRecognition();
            
            // 开始语音识别
            this.recognition.start();
            
            this.isRecording = true;
            this.updateUI();
            this.showStatus('正在录音... 请说话', true);
            this.permissionInfo.style.display = 'none';
            
        } catch (error) {
            this.showError('录音开始失败: ' + error.message);
            this.isRecording = false;
            this.updateUI();
        }
    }
    
    stopRecording() {
        try {
            if (this.recognition) {
                this.recognition.stop();
            }
            
            this.isRecording = false;
            this.updateUI();
            if (this.finalTranscript.trim()) {
                this.showRecognizedText(this.finalTranscript);
                this.showLoading(true);
                this.showStatus('正在处理文本...', false);
                
                // 发送到Python后端处理
                this.processTextWithPython(this.finalTranscript);
            } else {
                this.showStatus('录音结束，未识别到语音', false);
            }
            
        } catch (error) {
            this.showError('录音停止失败: ' + error.message);
        }
    }
    
    initSpeechRecognition() {
        // 使用Web Speech API
        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        this.recognition = new SpeechRecognition();
        
        this.recognition.continuous = true;
        this.recognition.interimResults = true;
        this.recognition.lang = 'zh-CN'; // 中文识别
        
        this.finalTranscript = '';
        
        this.recognition.onresult = (event) => {
            let interimTranscript = '';
            
            for (let i = event.resultIndex; i < event.results.length; i++) {
                const transcript = event.results[i][0].transcript;
                if (event.results[i].isFinal) {
                    this.finalTranscript += transcript;
                } else {
                    interimTranscript += transcript;
                }
            }
            
            // 显示临时结果
            if (interimTranscript) {
                this.showStatus(`识别中: ${this.finalTranscript + interimTranscript}`, true);
            } else if (this.finalTranscript) {
                this.showStatus(`已识别: ${this.finalTranscript}`, true);
            }
        };
        
        this.recognition.onerror = (event) => {
            console.error('语音识别错误:', event.error);
            this.showError(`语音识别错误: ${event.error}`);
            this.isRecording = false;
            this.updateUI();
        };
        
        this.recognition.onend = () => {
            // 语音识别自动结束时的处理
            if (this.isRecording) {
                this.isRecording = false;}
                this.updateUI();
                this.showStatus('录音结束', false);
                
                if (this.finalTranscript.trim()) {
                    this.showRecognizedText(this.finalTranscript);
                    this.showLoading(true);
                    this.processTextWithPython(this.finalTranscript);
                }
            
        };
    }
    
    async processTextWithPython(text) {
        try {
            const response = await fetch('/process_text', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ text: text })
            });
            
            const data = await response.json();
            
            if (data.status === 'success') {
                this.showResult(data);
            } else {
                this.showError(data.message);
            }
        } catch (error) {
            this.showError('文本处理失败: ' + error.message);
        } finally {
            this.showLoading(false);
        }
    }
    
    updateUI() {
        if (this.isRecording) {
            this.recordButton.textContent = '结束录音';
            this.recordButton.classList.add('recording');
        } else {
            this.recordButton.textContent = '开始录音';
            this.recordButton.classList.remove('recording');
        }
    }
    
    showStatus(message, isRecording) {
        this.statusElement.textContent = message;
        if (isRecording) {
            this.statusElement.classList.add('recording');
        } else {
            this.statusElement.classList.remove('recording');
        }
    }
    
    showRecognizedText(text) {
        this.textContent.textContent = text;
        this.recognizedText.style.display = 'block';
    }
    
    hideRecognizedText() {
        this.recognizedText.style.display = 'none';
    }
    
    showLoading(show) {
        this.loadingElement.style.display = show ? 'block' : 'none';
    }
    
    showResult(result) {
        document.getElementById('ai-response').textContent = result.result;
        
        this.resultElement.style.display = 'block';
    }
    
    hideResult() {
        this.resultElement.style.display = 'none';
    }
    
    showError(message) {
        this.errorMessage.textContent = message;
        this.errorMessage.style.display = 'block';
        setTimeout(() => {
            this.hideError();
        }, 5000);
    }
    
    hideError() {
        this.errorMessage.style.display = 'none';
    }
}

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', () => {
    new VoiceRecognitionApp();
});

$('forward').addEventListener('click', () => {
    fetch('/move_forward', { method: 'POST' });
});
$('backward').addEventListener('click', () => {
    fetch('/move_backward', { method: 'POST' });
});
$('left').addEventListener('click', () => {
    fetch('/turn_left', { method: 'POST' });
});
$('right').addEventListener('click', () => {
    fetch('/turn_right', { method: 'POST' });
});