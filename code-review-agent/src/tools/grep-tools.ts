import { execSync } from 'child_process';
import * as fs from 'fs';
import * as path from 'path';

/**
 * Search tools for finding patterns in code
 */
export const grepTools = {
  /**
   * Search file contents using regex patterns
   * Uses ripgrep (rg) if available, falls back to native search
   */
  async searchContent(
    pattern: string,
    searchPath?: string,
    globFilter?: string,
    fileType?: string
  ): Promise<string> {
    // Try using ripgrep first
    try {
      return this.ripgrepSearch(pattern, searchPath, globFilter, fileType);
    } catch (error) {
      // Fallback to native Node.js search
      console.warn('Ripgrep not available, using native search');
      return this.nativeSearch(pattern, searchPath, globFilter);
    }
  },

  /**
   * Search using ripgrep (faster)
   */
  ripgrepSearch(
    pattern: string,
    searchPath?: string,
    globFilter?: string,
    fileType?: string
  ): string {
    try {
      let command = `rg "${pattern}" --color=never --line-number`;

      if (searchPath) {
        command += ` "${searchPath}"`;
      }

      if (globFilter) {
        command += ` --glob="${globFilter}"`;
      }

      if (fileType) {
        command += ` --type=${fileType}`;
      }

      // Exclude common directories
      command += ' --glob="!node_modules" --glob="!dist" --glob="!.git"';

      const result = execSync(command, {
        encoding: 'utf-8',
        maxBuffer: 10 * 1024 * 1024, // 10MB buffer
      });

      return result || 'No matches found';
    } catch (error: any) {
      // rg returns exit code 1 if no matches found
      if (error.status === 1) {
        return 'No matches found';
      }
      throw error;
    }
  },

  /**
   * Fallback native search implementation
   */
  async nativeSearch(
    pattern: string,
    searchPath?: string,
    globFilter?: string
  ): Promise<string> {
    const basePath = searchPath ?? process.cwd();
    const regex = new RegExp(pattern, 'gm');
    const results: string[] = [];

    const searchFile = (filePath: string) => {
      try {
        const content = fs.readFileSync(filePath, 'utf-8');
        const lines = content.split('\n');

        lines.forEach((line, idx) => {
          if (regex.test(line)) {
            results.push(`${filePath}:${idx + 1}:${line}`);
          }
        });
      } catch (error) {
        // Skip files that can't be read
      }
    };

    const walkDirectory = (dir: string) => {
      try {
        const entries = fs.readdirSync(dir, { withFileTypes: true });

        for (const entry of entries) {
          const fullPath = path.join(dir, entry.name);

          // Skip excluded directories
          if (entry.isDirectory()) {
            if (['node_modules', 'dist', '.git', '.next'].includes(entry.name)) {
              continue;
            }
            walkDirectory(fullPath);
          } else {
            // Apply glob filter if specified
            if (globFilter) {
              const matchesGlob = new RegExp(
                globFilter.replace(/\*/g, '.*').replace(/\?/g, '.')
              ).test(entry.name);
              if (!matchesGlob) continue;
            }
            searchFile(fullPath);
          }
        }
      } catch (error) {
        // Skip directories that can't be read
      }
    };

    const stats = fs.statSync(basePath);
    if (stats.isDirectory()) {
      walkDirectory(basePath);
    } else {
      searchFile(basePath);
    }

    return results.length > 0 ? results.join('\n') : 'No matches found';
  },
};
