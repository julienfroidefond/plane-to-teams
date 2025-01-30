"""
Test script to format Plane issues into Teams message and send it.
"""
import json
import logging
import sys

from plane_to_teams.config import Config
from plane_to_teams.logger import setup_logging
from plane_to_teams.plane_client import PlaneClient
from plane_to_teams.teams_client import TeamsClient
from plane_to_teams.teams_formatter import format_issues

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
        # Create clients and fetch issues
        plane_client = PlaneClient(config)
        teams_client = TeamsClient(config.teams_webhook_url)
        
        issues = plane_client.get_issues()
        
        # Format issues into Teams message
        message = format_issues(issues)
        
        # Print formatted message
        print("\nFormatted Teams Message:")
        print("=" * 50)
        print(f"Title: {message.title}")
        print("-" * 50)
        for item in message.items:
            print(item)
        print("=" * 50)
        
        # Print raw JSON for Teams
        print("\nRaw Teams Message JSON:")
        print(json.dumps(message.to_dict(), indent=2))
        
        # Send message to Teams
        print("\nSending message to Teams...")
        teams_client.send_message(message)
        print("Message sent successfully!")
        
        return 0
        
    except Exception as e:
        print(f"Error: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 