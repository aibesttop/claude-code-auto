from claude_code_sdk import ClaudeSDKClient, ClaudeCodeOptions, AssistantMessage, TextBlock, ResultMessage
import asyncio
import logging
import datetime

# 配置日志
class SessionLogFilter(logging.Filter):
    """添加 session_id 到日志记录"""
    def __init__(self, session_id='N/A'):
        super().__init__()
        self.session_id = session_id
    
    def filter(self, record):
        record.session_id = self.session_id
        return True

# 初始化日志配置
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# 为我们的logger创建自定义格式器，包含session_id
class SessionFormatter(logging.Formatter):
    """自定义格式器，支持session_id"""
    def format(self, record):
        # 确保record有session_id属性
        if not hasattr(record, 'session_id'):
            record.session_id = getattr(self, 'session_id', 'N/A')
        return super().format(record)

# 配置我们的logger使用session格式
handler = logging.StreamHandler()
handler.setFormatter(SessionFormatter('%(asctime)s - %(levelname)s - [Session: %(session_id)s] - %(message)s', datefmt='%Y-%m-%d %H:%M:%S'))
logger.handlers.clear()
logger.addHandler(handler)
logger.propagate = False

# 会话ID生成器
async def step1(cwd_dir="/Users/zhangsan/cccc/demo_act", user_input="写一个python程序来设计一个加法,把理念写成md文档. 禁止书写任何python代码"):
    """
    执行交互式会话并返回是否成功完成
    Args:
        cwd_dir: 工作目录路径
        user_input: 用户输入的查询内容
    Returns:
        tuple: (success: bool, session_id: str)
    """
    # 确保目录存在
    import os
    os.makedirs(cwd_dir, exist_ok=True)
    
    # 创建带会话ID的logger（初始时使用临时ID）
    temp_session_id = f"temp_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}"
    session_logger = logging.getLogger(f"{__name__}.{temp_session_id}")
    session_logger.setLevel(logger.level)
    session_handler = logging.StreamHandler()
    session_formatter = SessionFormatter('%(asctime)s - %(levelname)s - [Session: %(session_id)s] - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
    session_formatter.session_id = temp_session_id
    session_handler.setFormatter(session_formatter)
    session_logger.addHandler(session_handler)
    session_logger.propagate = False
    
    # 使用最高权限模式
    options = ClaudeCodeOptions(
        permission_mode='bypassPermissions',  # 绕过所有权限检查
        # 不指定 allowed_tools 意味着允许所有工具
        cwd=cwd_dir
    )
    
    async with ClaudeSDKClient(options=options) as client:
        
        session_logger.debug("🚀 开始会话")
        session_logger.debug(f"📝 用户输入: {user_input}")
        session_logger.debug("=" * 50)
        
        # 存储真实的session_id
        real_session_id = None
        
        # 发送查询并监听响应
        await client.query(user_input)
        
        # 处理响应并判断会话是否完成
        conversation_complete = False
        message_count = 0
        
        async for message in client.receive_response():
            message_count += 1
            session_logger.debug(f"\n📨 [消息 {message_count}] 收到响应")
            
            # 检查是否为初始化消息以获取session_id
            if hasattr(message, 'subtype') and message.subtype == 'init':
                real_session_id = message.data.get('session_id')
                if real_session_id:
                    # 更新logger使用真实的session_id
                    session_formatter.session_id = real_session_id
                    session_logger.name = f"{__name__}.{real_session_id}"
                    
                    # 保存真实的session_id到文件
                    session_file_path = os.path.join(cwd_dir, "session_id.txt")
                    with open(session_file_path, 'w', encoding='utf-8') as f:
                        f.write(real_session_id)
                    
                    session_logger.debug(f"📝 获取到真实Session ID: {real_session_id}")
                    session_logger.debug(f"📁 Session ID已写入: {session_file_path}")
            
            if isinstance(message, AssistantMessage):
                session_logger.debug(f"🤖 类型: AssistantMessage")
                for i, block in enumerate(message.content):
                    if isinstance(block, TextBlock):
                        session_logger.debug(f"   [文本块 {i+1}]:")
                        session_logger.debug(f"   {block.text}")
                    else:
                        session_logger.debug(f"   [其他块 {i+1}]: {type(block).__name__}")
            
            elif isinstance(message, ResultMessage):
                session_logger.debug(f"✅ 类型: ResultMessage")
                session_logger.debug(f"   结果: {message}")
                conversation_complete = True
                session_logger.debug("=" * 50)
                session_logger.debug("🎉 会话已完成")
                break
            
            else:
                session_logger.debug(f"❓ 未知消息类型: {type(message).__name__}")
        
        if not conversation_complete:
            session_logger.debug("\n⚠️  会话未正常完成")
        
        # 使用真实的session_id，如果没有获取到则使用临时ID
        final_session_id = real_session_id if real_session_id else temp_session_id
        return conversation_complete, final_session_id

async def main():
    """
    主函数 - 返回简单的 yes/no
    """
    try:
        result, session_id = await step1()
        logger.info(f"会话ID: {session_id}")
        logger.info(f"最终结果: {'Yes' if result else 'No'}")
        
        # 输出JSON格式结果（便于其他程序解析）
        if "--json" in sys.argv:
            import json
            output = {
                "success": result,
                "session_id": session_id,
                "result": "Yes" if result else "No"
            }
            print(json.dumps(output, ensure_ascii=False))
        else:
            print(f"Session ID: {session_id}")
            print("Yes" if result else "No")
        
        return result
    except Exception as e:
        logger.error(f"❌ 发生错误: {e}")
        if "--json" in sys.argv:
            import json
            output = {
                "success": False,
                "error": str(e),
                "result": "No"
            }
            print(json.dumps(output, ensure_ascii=False))
        else:
            print("No")
        return False

if __name__ == "__main__":
    # 可通过命令行参数控制日志级别
    import sys
    if "--debug" in sys.argv:
        logging.getLogger().setLevel(logging.DEBUG)
        logger.info("Debug模式已启用")
    
    asyncio.run(main())