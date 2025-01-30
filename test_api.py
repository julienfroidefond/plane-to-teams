"""
Simple script to test Plane API.
"""
import logging
import sys

from plane_to_teams.config import Config
from plane_to_teams.logger import setup_logging
from plane_to_teams.plane_client import PlaneClient

def main():
    """Main function."""
    # Load and validate config
    config = Config.from_env()
    error = config.validate()
    if error:
        print(f"Configuration error: {error}")
        return 1

    # Setup logging
    setup_logging(config)
    
    try:
        # Create client and fetch issues
        client = PlaneClient(config)
        issues = client.get_issues()
        
        print(f"\nTotal issues found: {len(issues)}")
        return 0
        
    except Exception as e:
        print(f"Error: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 