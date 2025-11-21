import asyncio, os
from claude_code_sdk import ClaudeSDKClient, ClaudeCodeOptions, AssistantMessage, TextBlock

async def main():
    opts = ClaudeCodeOptions(permission_mode='bypassPermissions', cwd=os.getcwd())
    async with ClaudeSDKClient(opts) as c:
        await c.query('Say OK once')
        res = ''
        async for m in c.receive_response():
            if isinstance(m, AssistantMessage):
                for b in m.content:
                    if isinstance(b, TextBlock):
                        res += b.text
        print('RESP', res)

asyncio.run(main())
