#!/usr/bin/env node

import Anthropic from '@anthropic-ai/sdk';
import { fileTools, grepTools } from './tools/index.js';
import { reviewPrompt } from './prompts/review-prompt.js';
import * as dotenv from 'dotenv';
import * as path from 'path';

// Load environment variables
dotenv.config();

/**
 * Agent configuration
 */
interface AgentConfig {
  model: string;
  maxTokens: number;
  temperature: number;
  systemPrompt: string;
}

const agentConfig: AgentConfig = {
  model: process.env.MODEL || 'claude-sonnet-4-5-20250929',
  maxTokens: parseInt(process.env.MAX_TOKENS || '8000'),
  temperature: parseFloat(process.env.TEMPERATURE || '0.3'),
  systemPrompt: reviewPrompt,
};

/**
 * Tool definitions for Claude
 */
const tools: Anthropic.Messages.Tool[] = [
  {
    name: 'read_file',
    description: 'Read the contents of a file from the filesystem. Returns file content with line numbers.',
    input_schema: {
      type: 'object' as const,
      properties: {
        file_path: {
          type: 'string',
          description: 'Absolute or relative path to the file to read',
        },
        limit: {
          type: 'number',
          description: 'Maximum number of lines to read (optional)',
        },
        offset: {
          type: 'number',
          description: 'Starting line number (optional, 0-indexed)',
        },
      },
      required: ['file_path'],
    },
  },
  {
    name: 'glob_files',
    description: 'Find files matching a glob pattern. Supports ** for recursive search, * for wildcards.',
    input_schema: {
      type: 'object' as const,
      properties: {
        pattern: {
          type: 'string',
          description: 'Glob pattern like "**/*.js", "src/**/*.ts", "*.json"',
        },
        path: {
          type: 'string',
          description: 'Base directory to search in (optional, defaults to current directory)',
        },
      },
      required: ['pattern'],
    },
  },
  {
    name: 'search_content',
    description: 'Search file contents using regex patterns. Returns matching lines with file paths and line numbers.',
    input_schema: {
      type: 'object' as const,
      properties: {
        pattern: {
          type: 'string',
          description: 'Regex pattern to search for (e.g., "TODO", "function.*export", "console\\.log")',
        },
        path: {
          type: 'string',
          description: 'File or directory to search in (optional)',
        },
        glob: {
          type: 'string',
          description: 'Glob pattern to filter files (e.g., "*.js", "**/*.ts")',
        },
        type: {
          type: 'string',
          description: 'File type to search: js, ts, py, java, etc.',
        },
      },
      required: ['pattern'],
    },
  },
  {
    name: 'get_file_info',
    description: 'Get metadata about a file (size, modification date, etc.)',
    input_schema: {
      type: 'object' as const,
      properties: {
        file_path: {
          type: 'string',
          description: 'Path to the file',
        },
      },
      required: ['file_path'],
    },
  },
];

/**
 * Execute a tool call
 */
async function executeTool(
  toolName: string,
  toolInput: Record<string, unknown>
): Promise<string> {
  console.log(`\n🔧 Executing: ${toolName}`, JSON.stringify(toolInput, null, 2));

  try {
    switch (toolName) {
      case 'read_file':
        return await fileTools.readFile(
          toolInput.file_path as string,
          toolInput.offset as number | undefined,
          toolInput.limit as number | undefined
        );

      case 'glob_files':
        return await fileTools.globFiles(
          toolInput.pattern as string,
          toolInput.path as string | undefined
        );

      case 'search_content':
        return await grepTools.searchContent(
          toolInput.pattern as string,
          toolInput.path as string | undefined,
          toolInput.glob as string | undefined,
          toolInput.type as string | undefined
        );

      case 'get_file_info':
        return await fileTools.getFileInfo(toolInput.file_path as string);

      default:
        return `Error: Unknown tool "${toolName}"`;
    }
  } catch (error) {
    return `Error executing ${toolName}: ${error instanceof Error ? error.message : String(error)}`;
  }
}

/**
 * Main agent loop with tool calling
 */
async function runReviewAgent(userMessage: string): Promise<void> {
  const apiKey = process.env.ANTHROPIC_API_KEY;
  if (!apiKey) {
    throw new Error('ANTHROPIC_API_KEY environment variable is required');
  }

  const client = new Anthropic({ apiKey });

  const messages: Anthropic.Messages.MessageParam[] = [
    { role: 'user', content: userMessage },
  ];

  console.log('\n🤖 Code Review Agent Started\n');
  console.log(`Model: ${agentConfig.model}`);
  console.log(`Max Tokens: ${agentConfig.maxTokens}`);
  console.log(`Temperature: ${agentConfig.temperature}\n`);
  console.log('─'.repeat(80));

  let iterationCount = 0;
  const maxIterations = 50; // Safety limit

  // Agentic loop
  while (iterationCount < maxIterations) {
    iterationCount++;
    console.log(`\n📍 Iteration ${iterationCount}/${maxIterations}`);

    const response = await client.messages.create({
      model: agentConfig.model,
      max_tokens: agentConfig.maxTokens,
      temperature: agentConfig.temperature,
      system: agentConfig.systemPrompt,
      tools: tools,
      messages: messages,
    });

    console.log(`Stop reason: ${response.stop_reason}`);

    // Add assistant response to message history
    messages.push({ role: 'assistant', content: response.content });

    // Check if agent is done
    if (response.stop_reason === 'end_turn') {
      console.log('\n' + '═'.repeat(80));
      console.log('📝 REVIEW COMPLETE');
      console.log('═'.repeat(80) + '\n');

      // Extract and display final text response
      const textBlocks = response.content.filter(
        (block): block is Anthropic.Messages.TextBlock => block.type === 'text'
      );

      for (const block of textBlocks) {
        console.log(block.text);
      }

      break;
    }

    // Process tool calls
    if (response.stop_reason === 'tool_use') {
      const toolResults: Anthropic.Messages.ToolResultBlockParam[] = [];

      for (const block of response.content) {
        if (block.type === 'tool_use') {
          const result = await executeTool(
            block.name,
            block.input as Record<string, unknown>
          );

          toolResults.push({
            type: 'tool_result',
            tool_use_id: block.id,
            content: result,
          });
        }
      }

      // Add tool results to message history
      messages.push({ role: 'user', content: toolResults });
    }

    // Handle max_tokens stop reason
    if (response.stop_reason === 'max_tokens') {
      console.warn('\n⚠️  Warning: Response truncated due to max_tokens limit');
      console.log('Consider increasing MAX_TOKENS in .env file\n');
      break;
    }
  }

  if (iterationCount >= maxIterations) {
    console.warn('\n⚠️  Warning: Reached maximum iteration limit');
  }

  console.log(`\n✅ Agent completed in ${iterationCount} iterations\n`);
}

/**
 * CLI entry point
 */
async function main() {
  const args = process.argv.slice(2);

  // Parse command line arguments
  let targetPath = process.cwd();
  let customPrompt = '';

  for (let i = 0; i < args.length; i++) {
    const arg = args[i];

    if (arg === '--path' || arg === '-p') {
      targetPath = path.resolve(args[++i]);
    } else if (arg === '--prompt' || arg === '-m') {
      customPrompt = args[++i];
    } else if (arg === '--help' || arg === '-h') {
      printHelp();
      process.exit(0);
    } else if (!arg.startsWith('-')) {
      targetPath = path.resolve(arg);
    }
  }

  // Build review request
  const reviewRequest = customPrompt || `
Please perform a comprehensive code review of the codebase in the directory: ${targetPath}

Focus on:
1. **Security vulnerabilities** (OWASP Top 10, authentication, authorization, input validation)
2. **Performance issues** (inefficient algorithms, memory leaks, blocking operations)
3. **Code quality** (SOLID principles, design patterns, maintainability, readability)
4. **Testing** (test coverage, missing tests, test quality)
5. **Best practices** (language-specific conventions, framework patterns)

Provide a detailed report with:
- Specific file paths and line numbers for each issue
- Severity ratings (Critical, High, Medium, Low)
- Concrete recommendations with code examples
- Positive observations about good practices

Start by exploring the codebase structure, then analyze the code systematically.
`;

  console.log(`\n🎯 Target: ${targetPath}`);

  try {
    await runReviewAgent(reviewRequest);
  } catch (error) {
    console.error('\n❌ Error:', error instanceof Error ? error.message : String(error));
    process.exit(1);
  }
}

/**
 * Print help message
 */
function printHelp() {
  console.log(`
Code Review Agent - AI-powered code analysis tool

Usage:
  npm start [options] [path]
  npm run dev [options] [path]

Options:
  -p, --path <path>      Path to codebase to review (default: current directory)
  -m, --prompt <text>    Custom review prompt
  -h, --help            Show this help message

Environment Variables:
  ANTHROPIC_API_KEY     Your Anthropic API key (required)
  MODEL                 Claude model to use (default: claude-sonnet-4-5-20250929)
  MAX_TOKENS            Maximum tokens for response (default: 8000)
  TEMPERATURE           Model temperature 0-1 (default: 0.3)

Examples:
  npm start                                    # Review current directory
  npm start ../my-project                      # Review specific directory
  npm start --path /path/to/code               # Review with explicit path
  npm start --prompt "Focus on security only"  # Custom review prompt

For more information, see README.md
`);
}

// Run if executed directly
if (import.meta.url === `file://${process.argv[1]}`) {
  main();
}

export { runReviewAgent, executeTool, tools, agentConfig };
