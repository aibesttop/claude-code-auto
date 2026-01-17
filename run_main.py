import os
import sys

# Set git bash path for Claude Code SDK on Windows
os.environ['CLAUDE_CODE_GIT_BASH_PATH'] = r'D:\Program Files\Git\bin\bash.exe'

# Run the main script
if __name__ == '__main__':
    with open('src/main.py', encoding='utf-8') as f:
        exec(f.read())
