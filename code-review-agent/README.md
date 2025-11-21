# Code Review Agent

An AI-powered code review agent built with the Claude Agent SDK. Automatically analyzes codebases for security vulnerabilities, performance issues, code quality problems, and best practices violations.

## Features

- **Comprehensive Analysis**: Security, performance, code quality, and testing coverage
- **Multi-Language Support**: JavaScript/TypeScript, Python, Java, Go, and more
- **Intelligent Tool Use**: Autonomous file discovery, content search, and pattern matching
- **Detailed Reports**: Structured output with severity ratings and specific recommendations
- **Agentic Workflow**: Self-directed exploration and analysis using Claude's reasoning

## What It Reviews

### Security
- OWASP Top 10 vulnerabilities
- Authentication and authorization issues
- Input validation and sanitization
- SQL/NoSQL injection risks
- XSS vulnerabilities
- Hardcoded secrets and API keys
- Dependency vulnerabilities

### Performance
- Algorithm efficiency (time/space complexity)
- Database query optimization (N+1 queries)
- Memory leaks and resource management
- Blocking operations
- Caching strategies
- Bundle size and optimization

### Code Quality
- SOLID principles adherence
- Design pattern usage
- Code duplication
- Function/class complexity
- Naming conventions
- Error handling
- Type safety (TypeScript)

### Testing
- Test coverage analysis
- Missing test cases
- Test quality and patterns
- Mock/stub usage

## Installation

### Prerequisites

- Node.js 18+
- npm, pnpm, yarn, or bun
- Anthropic API key ([get one here](https://console.anthropic.com/))
- (Optional) [ripgrep](https://github.com/BurntSushi/ripgrep) for faster searching

### Setup

1. Clone or download this repository

2. Install dependencies:
```bash
npm install
```

3. Create your `.env` file:
```bash
cp .env.example .env
```

4. Add your Anthropic API key to `.env`:
```env
ANTHROPIC_API_KEY=your_api_key_here
```

5. Build the project:
```bash
npm run build
```

## Usage

### Basic Usage

Review current directory:
```bash
npm start
```

Review a specific directory:
```bash
npm start ../my-project
```

Or with explicit path:
```bash
npm start --path /path/to/codebase
```

### Advanced Usage

Custom review prompt:
```bash
npm start --prompt "Focus only on security vulnerabilities in the authentication module"
```

Development mode (with auto-reload):
```bash
npm run dev ../my-project
```

### Command-Line Options

```
Options:
  -p, --path <path>      Path to codebase to review (default: current directory)
  -m, --prompt <text>    Custom review prompt
  -h, --help            Show help message
```

### Environment Variables

Configure in `.env` file:

```env
# Required
ANTHROPIC_API_KEY=your_api_key_here

# Optional (with defaults)
MODEL=claude-sonnet-4-5-20250929
MAX_TOKENS=8000
TEMPERATURE=0.3
LOG_LEVEL=info
```

### Model Options

Choose based on your needs:

- `claude-opus-4-1-20250805` - Most capable, best for complex codebases (slower, more expensive)
- `claude-sonnet-4-5-20250929` - **Recommended** - Balanced speed and quality
- `claude-haiku-4-5-20251001` - Fastest, good for quick reviews

## How It Works

The agent follows an **agentic workflow**:

1. **Discovery Phase**
   - Explores codebase structure using `glob_files`
   - Identifies project type, languages, and frameworks
   - Locates configuration files and entry points

2. **Analysis Phase**
   - Reads source files using `read_file`
   - Searches for patterns using `search_content`
   - Analyzes security, performance, and quality issues
   - Cross-references dependencies and imports

3. **Reporting Phase**
   - Categorizes findings by severity
   - Provides specific file paths and line numbers
   - Suggests concrete fixes with code examples
   - Highlights positive observations

### Agentic Loop

The agent uses Claude's **tool calling** in an autonomous loop:

```
User Request → Claude thinks → Calls tools → Processes results →
Thinks more → Calls more tools → ... → Final report
```

This allows the agent to:
- Explore the codebase independently
- Follow leads and investigate patterns
- Make connections across files
- Provide context-aware recommendations

## Example Output

```markdown
# Code Review Report

## Executive Summary
Reviewed a React + TypeScript web application with 45 source files.
Found 12 issues across security, performance, and code quality categories.

## Critical Issues 🔴

**Issue:** Hardcoded API key in configuration file
- **Location:** src/config/api.ts:12
- **Severity:** Critical
- **Impact:** API key exposed in source code could be stolen
- **Recommendation:** Move to environment variable
  ```typescript
  // Before
  const API_KEY = "sk_live_abc123...";

  // After
  const API_KEY = process.env.REACT_APP_API_KEY;
  ```

## High Priority Issues 🟠
...

## Metrics
- Files reviewed: 45
- Total issues found: 12
- Critical: 1 | High: 3 | Medium: 5 | Low: 3
```

## Available Tools

The agent has access to these tools:

### `read_file(file_path, offset?, limit?)`
Reads file contents with optional line range.

### `glob_files(pattern, path?)`
Finds files matching glob patterns:
- `**/*.ts` - All TypeScript files recursively
- `src/**/*.{js,jsx}` - JS/JSX files in src/
- `*.json` - JSON files in current directory

### `search_content(pattern, path?, glob?, type?)`
Searches code using regex patterns:
- `pattern`: Regex to search for
- `path`: Limit to specific file/directory
- `glob`: Filter by file pattern
- `type`: Filter by file type (js, ts, py, etc.)

### `get_file_info(file_path)`
Gets file metadata (size, modified date, etc.)

## Project Structure

```
code-review-agent/
├── src/
│   ├── agent.ts              # Main agent with agentic loop
│   ├── tools/
│   │   ├── file-tools.ts     # File reading and globbing
│   │   ├── grep-tools.ts     # Content search
│   │   └── index.ts          # Tool exports
│   ├── prompts/
│   │   └── review-prompt.ts  # System prompt for agent
│   └── utils/
├── dist/                     # Compiled output
├── package.json
├── tsconfig.json
├── .env                      # Your configuration (not in git)
├── .env.example              # Template configuration
└── README.md
```

## Development

### Building

```bash
npm run build
```

### Running in Dev Mode

```bash
npm run dev [path]
```

### Cleaning Build

```bash
npm run clean
```

### Adding Custom Tools

To add new tools, edit `src/agent.ts`:

1. Add tool definition to `tools` array
2. Implement tool function in `src/tools/`
3. Add case in `executeTool()` function
4. Update system prompt if needed

Example:
```typescript
// 1. Add tool definition
{
  name: 'count_lines',
  description: 'Count lines of code in a file',
  input_schema: {
    type: 'object',
    properties: {
      file_path: { type: 'string' }
    },
    required: ['file_path']
  }
}

// 2. Add execution case
case 'count_lines':
  return await customTools.countLines(toolInput.file_path as string);
```

## Integration with Claude Code

To use this agent as a custom command in Claude Code:

1. Create `.claude/commands/review.json`:
```json
{
  "name": "review",
  "description": "Run AI code review on current directory",
  "command": "cd ${workspaceFolder}/code-review-agent && npm start ${workspaceFolder}"
}
```

2. Use in Claude Code:
```
/review
```

## Troubleshooting

### "ANTHROPIC_API_KEY not found"
Make sure you've created a `.env` file with your API key.

### "ripgrep not found"
The agent will fall back to native Node.js search. For better performance, install ripgrep:
- macOS: `brew install ripgrep`
- Ubuntu: `apt install ripgrep`
- Windows: `choco install ripgrep`

### "Response truncated"
Increase `MAX_TOKENS` in `.env` file:
```env
MAX_TOKENS=16000
```

### "Rate limit exceeded"
Your API key has hit rate limits. Wait or upgrade your Anthropic plan.

## Limitations

- Maximum codebase size depends on token limits
- Very large files (>10000 lines) may be truncated
- Binary files are ignored
- Some language-specific patterns may not be detected

## Roadmap

- [ ] Support for more programming languages
- [ ] Integration with CI/CD pipelines
- [ ] Custom rule configuration
- [ ] Export to multiple formats (JSON, HTML, PDF)
- [ ] Incremental reviews (only changed files)
- [ ] Team collaboration features
- [ ] Web UI dashboard

## Contributing

Contributions welcome! Areas to improve:

1. Add language-specific analyzers
2. Enhance security pattern detection
3. Improve performance analysis
4. Add more tool integrations
5. Better report formatting

## License

MIT License - see LICENSE file for details

## Credits

Built with:
- [Claude Agent SDK](https://docs.anthropic.com/claude/docs) by Anthropic
- [Anthropic SDK](https://github.com/anthropics/anthropic-sdk-typescript)
- [glob](https://github.com/isaacs/node-glob)
- [ripgrep](https://github.com/BurntSushi/ripgrep) (optional)

## Support

For issues or questions:
- Open an issue on GitHub
- Check the [Claude documentation](https://docs.anthropic.com/)
- Review example prompts in `src/prompts/`

---

**Happy Code Reviewing!** 🚀
