import * as fs from 'fs';
import * as path from 'path';
import { glob } from 'glob';

/**
 * File reading and discovery tools for the code review agent
 */
export const fileTools = {
  /**
   * Read file contents with optional line range
   */
  async readFile(
    filePath: string,
    offset?: number,
    limit?: number
  ): Promise<string> {
    try {
      const absolutePath = path.resolve(filePath);

      // Check if file exists
      if (!fs.existsSync(absolutePath)) {
        return `Error: File not found at ${absolutePath}`;
      }

      const content = fs.readFileSync(absolutePath, 'utf-8');
      const lines = content.split('\n');

      const startLine = offset ?? 0;
      const endLine = limit ? startLine + limit : lines.length;
      const selectedLines = lines.slice(startLine, endLine);

      // Format with line numbers (using cat -n format)
      return selectedLines
        .map((line, idx) => `${startLine + idx + 1}\t${line}`)
        .join('\n');
    } catch (error) {
      return `Error reading file: ${error instanceof Error ? error.message : String(error)}`;
    }
  },

  /**
   * Find files matching a glob pattern
   */
  async globFiles(pattern: string, basePath?: string): Promise<string> {
    try {
      const searchPath = basePath ?? process.cwd();

      const matches = await glob(pattern, {
        cwd: searchPath,
        absolute: true,
        ignore: ['**/node_modules/**', '**/dist/**', '**/.git/**'],
      });

      if (matches.length === 0) {
        return `No files matched pattern: ${pattern} in ${searchPath}`;
      }

      // Sort by modification time (most recent first)
      const filesWithStats = matches.map(file => ({
        path: file,
        mtime: fs.statSync(file).mtime.getTime()
      }));

      filesWithStats.sort((a, b) => b.mtime - a.mtime);

      return filesWithStats.map(f => f.path).join('\n');
    } catch (error) {
      return `Error globbing files: ${error instanceof Error ? error.message : String(error)}`;
    }
  },

  /**
   * Get file metadata
   */
  async getFileInfo(filePath: string): Promise<string> {
    try {
      const absolutePath = path.resolve(filePath);

      if (!fs.existsSync(absolutePath)) {
        return `Error: File not found at ${absolutePath}`;
      }

      const stats = fs.statSync(absolutePath);
      const ext = path.extname(absolutePath);

      return JSON.stringify({
        path: absolutePath,
        size: stats.size,
        modified: stats.mtime,
        created: stats.birthtime,
        extension: ext,
        isDirectory: stats.isDirectory(),
      }, null, 2);
    } catch (error) {
      return `Error getting file info: ${error instanceof Error ? error.message : String(error)}`;
    }
  }
};
