import os
import shutil
from claude_code_sdk import ClaudeSDKClient, ClaudeCodeOptions, AssistantMessage, TextBlock
import asyncio

async def step2(directory: str, goal: str, work_dir: str) -> tuple[bool, str]:
    """
    将 work_dir 复制到 directory 下，重命名为 {原名}_mirror
    并使用 Claude 检查目标完成状态
    :param directory: 目标目录
    :param goal: 目标描述
    :param work_dir: 要复制的工作目录
    :return: [bool, str] - 是否完成，下一次要发出去的提示词
    """
    # 确保目标目录存在
    os.makedirs(directory, exist_ok=True)

    # 计算目标路径
    base_name = os.path.basename(work_dir.rstrip("/"))
    dst = os.path.join(directory, f"{base_name}_mirror")

    # 如果已存在，提示并删除（或自行处理）
    if os.path.exists(dst):
        print(f"⚠️ 目标文件夹已存在: {dst}，将删除后重建")
        shutil.rmtree(dst)

    # 执行复制
    shutil.copytree(work_dir, dst)
    
    # 删除复制过来的 session_id.txt 文件
    copied_session_file = os.path.join(dst, "session_id.txt")
    if os.path.exists(copied_session_file):
        os.remove(copied_session_file)
        print(f"🗑️ 已删除会话文件: {copied_session_file}")

    print(f"✅ 已复制 {work_dir} -> {dst}")
    print(f"📌 任务目标: {goal}")

    # 第二步：使用 Claude 检查执行目标
    
    # 配置 Claude SDK 选项
    options = ClaudeCodeOptions(
        permission_mode='bypassPermissions',  # 绕过权限检查
        cwd=dst  # 设置工作目录为拷贝后的目录
    )
    
    # 使用 Claude SDK 客户端
    async with ClaudeSDKClient(options) as client:
        # 修改后的提示词，用于检查执行目标
        prompt = f"""
        根据我们之前的对话，请检查以下目标是否已经完成：
        
        目标：{goal}
        
        请以JSON格式回复，包含以下字段：
        - completed: 布尔值，表示目标是否已完成
        - next_prompt: 字符串，如果未完成，描述下一步应该做什么
        - analysis: 字符串，对当前状态的分析

        示例格式：
        {{
            "completed": true,
            "next_prompt": "",
            "analysis": "目标已完成"
        }}
        """
        
        await client.query(prompt)  # 发送查询
        
        # 接收并处理响应
        response_text = ""
        async for message in client.receive_response():
            if isinstance(message, AssistantMessage):  # 如果是助手消息
                for block in message.content:  # 遍历消息内容块
                    if isinstance(block, TextBlock):  # 如果是文本块
                        print(f"Claude: {block.text}")  # 打印 Claude 的回复
                        response_text += block.text + "\n"
        
        # 解析JSON响应
        import json
        try:
            # 尝试从响应中提取JSON部分
            start_idx = response_text.find("{")
            end_idx = response_text.rfind("}") + 1
            if start_idx != -1 and end_idx != 0:
                json_str = response_text[start_idx:end_idx]
                result = json.loads(json_str)
                goal_completed = result.get("completed", False)
                next_prompt = result.get("next_prompt", "")
                print(f"✅ 解析结果: completed={goal_completed}, next_prompt='{next_prompt}'")
            else:
                print("❌ 未找到有效的JSON响应")
                goal_completed = False
                next_prompt = "响应格式错误，无法解析"
        except json.JSONDecodeError as e:
            print(f"❌ JSON解析失败: {e}")
            goal_completed = False
            next_prompt = f"JSON解析错误: {str(e)}"
        
        return [goal_completed, next_prompt]

# 示例调用
if __name__ == "__main__":
    import asyncio
    result = asyncio.run(step2(
        directory="/Users/zhangsan/cccc/mirror",  
        goal="写一个python程序来设计一个加法",  
        work_dir="/Users/zhangsan/cccc/demo_act"  
    ))
    print(f"返回结果: {result}")