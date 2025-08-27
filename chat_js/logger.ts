// Custom logger with automatic line numbers and timestamps
class Logger {
  constructor() {
    // Override console methods to include line numbers
    this.overrideConsole();
  }

  overrideConsole() {
    const originalLog = console.log;
    const originalWarn = console.warn;
    const originalError = console.error;
    const originalInfo = console.info;
    const originalDebug = console.debug;

    // Helper function to get line number
    const getLineNumber = () => {
      const stack = new Error().stack;
      if (!stack) return '??';
      
      const lines = stack.split('\n');
      
      // Skip the first few lines that are from our logger
      // Start from line 4 to skip: Error constructor, getLineNumber, formatMessage, and the console override
      for (let i = 4; i < lines.length; i++) {
        const line = lines[i];
        if (!line) continue;
        
        // Skip lines that contain our logger file
        if (line.includes('logger.ts')) {
          continue;
        }
        
        // Look for any file path with line numbers
        if (line.includes(':') && (line.includes('.js') || line.includes('.ts'))) {
          const match = line.match(/:(\d+):\d+\)?$/);
          if (match) {
            // Extract filename for better context
            const fileMatch = line.match(/([^/\\]+\.(?:js|ts)):/);
            const filename = fileMatch ? fileMatch[1] : 'unknown';
            return `${filename}:${match[1]}`;
          }
        }
      }
      return '??';
    };

    // Helper function to format log message
    const formatMessage = (level: string, args: any[]) => {
      const timestamp = new Date().toISOString();
      const lineNumber = getLineNumber();
      const prefix = `[${timestamp}] [${lineNumber}] [${level}]`;
      
      // Convert all arguments to strings and join them
      const message = args.map((arg: any) => 
        typeof arg === 'object' ? JSON.stringify(arg, null, 2) : String(arg)
      ).join(' ');
      
      return `${prefix} ${message}`;
    };

    // Override console.log
    console.log = (...args) => {
      originalLog(formatMessage('LOG', args));
    };

    // Override console.warn
    console.warn = (...args) => {
      originalWarn(formatMessage('WARN', args));
    };

    // Override console.error
    console.error = (...args) => {
      originalError(formatMessage('ERROR', args));
    };

    // Override console.info
    console.info = (...args) => {
      originalInfo(formatMessage('INFO', args));
    };

    // Override console.debug
    console.debug = (...args) => {
      originalDebug(formatMessage('DEBUG', args));
    };
  }

  // Method to restore original console methods if needed
  restoreConsole() {
    // This would restore the original console methods
    // Useful for testing or if you need to disable the custom logger
  }
}

// Create and export logger instance
const logger = new Logger();
export default logger; 