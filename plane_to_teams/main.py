"""
Main application entry point.
"""
import logging
import sys

from plane_to_teams.config import Config
from plane_to_teams.logger import setup_logging

def main() -> int:
    """
    Main application entry point.
    
    Returns:
        int: Exit code
    """
    try:
        # Load configuration
        config = Config.from_env()
        
        # Validate configuration
        error = config.validate()
        if error:
            print(f"Configuration error: {error}", file=sys.stderr)
            return 1
        
        # Setup logging
        setup_logging(config)
        
        logging.info("Application started")
        
        # TODO: Implement main application logic
        
        return 0
        
    except Exception as e:
        print(f"Fatal error: {e}", file=sys.stderr)
        return 1

if __name__ == "__main__":
    sys.exit(main()) 