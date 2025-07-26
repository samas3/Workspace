from utils import util
class CommandParser:
    """指令解析系统，识别并执行预定义指令"""
    
    COMMAND_MAP = {
        "拍照": {
            "handler": "take_photo",
            "description": "执行拍照流程",
            "example": "帮我拍张照片"
        },
        # 可以继续添加更多指令
    }
    
    def __init__(self):
        """初始化指令解析器
        """
        pass
        
    def parse_command(self, command_text):
        """解析指令文本
        
        Args:
            command_text: 指令文本
            
        Returns:
            dict: 解析结果 {
                "success": bool,
                "command": str,
                "params": list,
                "handler": str
            }
        """
        for cmd in self.COMMAND_MAP:
            if cmd in command_text:
                params = self.extract_params(command_text, cmd)
                return {
                    "success": True,
                    "command": cmd,
                    "params": params,
                    "handler": self.COMMAND_MAP[cmd]["handler"]
                }
        return {"success": False}
        
    def extract_params(self, text, command):
        """从指令文本中提取参数
        
        Args:
            text: 完整指令文本
            command: 指令关键词
            
        Returns:
            list: 参数列表
        """
        # TODO: 实现更复杂的参数提取逻辑
        return [text.replace(command, "").strip()]
        
    def execute_command(self, command_info):
        """执行解析后的指令
        
        Args:
            command_info: parse_command的返回结果
            
        Returns:
            str: 执行结果文本
        """
        if not command_info["success"]:
            return "无法识别的指令"
            
        handler = getattr(self, command_info["handler"])
        result = handler(*command_info["params"])
        return self.format_response(command_info["command"], result)
    def take_photo(self, *args, **kwargs):
        """执行拍照指令
        """
        util.capture_photo()
        return "已拍照"
        
    def format_response(self, command, result):
        """格式化指令响应
        
        Args:
            command: 指令名称
            result: 执行结果
            
        Returns:
            str: 格式化后的响应文本
        """
        return f"{self.COMMAND_MAP[command]['description']}: {result}"
