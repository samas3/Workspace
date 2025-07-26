import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from services import ai
import yaml
from core import command_parser
class AIConversation:
    """AI对话核心类，负责处理用户对话请求"""
    
    def __init__(self, system='system'):
        """初始化AI对话系统
        """
        with open('config/settings.yaml', 'r', encoding='utf-8') as f:
            yml = yaml.load(f, Loader=yaml.FullLoader)
        self.ai = ai.AI(yml['ai']['API_KEY'], yml['ai']['BASE_URL'], yml['ai'][system], yml['ai']['model'])
        self.parser = command_parser.CommandParser()
        
    def process_input(self, user_input):
        """处理用户输入
        
        Args:
            user_input: 用户输入文本
            
        Returns:
            str: AI响应文本
        """
        if (res := self.parse_command(user_input)):
            return self.process_command(res)
        else:
            return self.process_chat(user_input)
            
    def parse_command(self, text):
        """判断输入是否为指令
        
        Args:
            text: 输入文本
            
        Returns:
            bool: 是否为指令
        """
        # TODO: 实现指令判断逻辑
        if self.parser.parse_command(text)["success"]:
            command_info = self.parser.parse_command(text)
            print(command_info)
            return command_info
        return None
        
    def process_command(self, command):
        """处理指令
        
        Args:
            command: 指令文本
            
        Returns:
            str: 指令执行结果
        """
        # TODO: 实现指令处理逻辑
        result = self.parser.execute_command(command)
        return result
        
    def process_chat(self, message):
        """处理聊天消息
        
        Args:
            message: 聊天消息
            
        Returns:
            str: AI响应
        """
        response = self.ai.get_response(message)
        return response


        