import asyncio
from step1 import step1
from step3 import main as step3_main

async def main():
    # Parameters
    cwd_dir = "/Users/zhangsan/cccc/demo_act"
    goal = "写一个python程序来设计一个加法"
    
    # Execute step1 first
    print("=== Executing Step 1 ===")
    await step1(
        cwd_dir=cwd_dir,
        user_input="写一个python程序来设计一个加法,把理念写成md文档. 禁止书写任何python代码"
    )
    
    # Then execute step3 main
    print("\n=== Executing Step 3 ===")
    # Note: step3's main uses hardcoded goal, so we'll modify it to accept parameter
    await step3_main(cwd_path=cwd_dir,goal=goal)

if __name__ == "__main__":
    asyncio.run(main())