
import asyncio
import sys
import os
from claude_code_sdk import ClaudeSDKClient, ClaudeCodeOptions

# Add the project root to python path
sys.path.append(os.getcwd())

async def run_sdk_query(i):
    print(f"--- Run {i} ---")
    options = ClaudeCodeOptions(
        permission_mode="bypassPermissions",
        cwd=os.getcwd()
    )
    
    print(f"Run {i}: Initializing client...")
    try:
        async with ClaudeSDKClient(options) as client:
            print(f"Run {i}: Connected. Querying...")
            await client.query("Hello, are you there?")
            
            print(f"Run {i}: Waiting for response...")
            async for message in client.receive_response():
                # Just consume
                pass
            print(f"Run {i}: Done.")
    except Exception as e:
        print(f"Run {i}: FAILED with {e}")

async def main():
    for i in range(1, 4):
        await run_sdk_query(i)
        print(f"Run {i}: Finished loop iteration.\n")
        await asyncio.sleep(2) # Wait a bit between runs

if __name__ == "__main__":
    asyncio.run(main())
