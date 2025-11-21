from claude_code_sdk import ClaudeSDKClient, ClaudeCodeOptions, AssistantMessage, TextBlock
import asyncio
import os
from step2 import step2

async def step3(cwd_path,goal):
    session_file = os.path.join(cwd_path, "session_id.txt")
    resume_session = ""
    
    if os.path.exists(session_file):
        with open(session_file, 'r') as f:
            resume_session = f.read().strip()
        print(f"Resume session from file: {resume_session}")
    else:
        print("No existing session file found")
    
    options = ClaudeCodeOptions(
        permission_mode='bypassPermissions',
        cwd=cwd_path,
        resume=resume_session  
    )
    
    real_session_id = None
    
    async with ClaudeSDKClient(options) as client:
        # Get prompt from step2
        exit_loop, prompt = await step2(
            directory="/Users/zhangsan/cccc/mirror",
            goal=goal,
            work_dir=cwd_path
        )
        
        if not exit_loop:
            await client.query(prompt)
            
            async for message in client.receive_response():
                if isinstance(message, AssistantMessage):
                    for block in message.content:
                        if isinstance(block, TextBlock):
                            print(f"Claude: {block.text}")
                    # Extract session_id from message data if available
                    if hasattr(message, 'data') and message.data:
                        real_session_id = message.data.get('session_id')
    
    # Update session_id.txt if we got a new session_id
    if real_session_id:
        with open(session_file, 'w') as f:
            f.write(real_session_id)
    
    return real_session_id, exit_loop

async def main(cwd_path = "/Users/zhangsan/cccc/demo_act",goal="写一个python程序来设计一个加法"):
    # Default cwd path
    
    while True:
        # Execute step3 with the current working directory
        session_id, exit_loop = await step3(cwd_path,goal=goal)
        
        if exit_loop:
            print("Exiting loop...")
            break
        
        print(f"Session completed. New session ID: {session_id}")

if __name__ == "__main__":
    asyncio.run(main())