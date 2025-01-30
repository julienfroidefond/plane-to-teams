"""
Teams message formatter for Plane issues.
"""
from dataclasses import dataclass
from typing import Dict, List, Tuple

from plane_to_teams.plane_client import PlaneIssue

PRIORITY_COLORS = {
    "urgent": "attention",  # Red
    "high": "warning",      # Orange
    "medium": "good",       # Green
    "low": "accent"         # Blue
}

STATE_NAMES = {
    "daaf8056-e88d-40ba-b527-d58f3e518059": "En cours",
    "9ce312cc-0018-4864-9867-064939dda809": "A faire",
    "6c15d246-3feb-4030-aa58-e1b98cd05b17": "En attente",
    "1d3cdf89-0efd-45ec-a50c-2b8c56db6344": "Bloqué",
    "a591fadc-7f1b-49c2-9ccd-43f50451e415": "En revue",
    "20df7a00-c8f5-4ae4-b9a3-8726946129b1": "A valider",
    "318803e3-f0ce-4dbf-b0b4-beb1cfba9e81": "Backlog",
    "ad3ab555-13e9-4ef5-901d-a64813915722": "Archivé",
    "e0b22f89-691a-4f4c-9083-3c860cb0255a": "Terminé"
}

# Map states to sort order
STATE_ORDER = {
    "daaf8056-e88d-40ba-b527-d58f3e518059": 0,  # En cours
    "9ce312cc-0018-4864-9867-064939dda809": 1,  # A faire
    "318803e3-f0ce-4dbf-b0b4-beb1cfba9e81": 2,  # Backlog
}

@dataclass
class TeamsMessage:
    """Represents a Teams message."""
    
    title: str
    items: List[Tuple[str, str, str, str]]  # (priority, name, state, url)
    
    def to_dict(self) -> Dict:
        """Convert to Teams message format.
        
        Returns:
            Dict: The message in Teams format
        """
        return {
            "type": "message",
            "attachments": [
                {
                    "contentType": "application/vnd.microsoft.card.adaptive",
                    "content": {
                        "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
                        "type": "AdaptiveCard",
                        "version": "1.2",
                        "body": [
                            {
                                "type": "Container",
                                "style": "emphasis",
                                "bleed": True,
                                "items": [
                                    {
                                        "type": "TextBlock",
                                        "text": "🎯 " + self.title,
                                        "size": "large",
                                        "weight": "bolder",
                                        "color": "accent",
                                        "horizontalAlignment": "center",
                                        "spacing": "large",
                                        "wrap": True
                                    }
                                ]
                            },
                            {
                                "type": "Container",
                                "bleed": True,
                                "items": [
                                    {
                                        "type": "ColumnSet",
                                        "columns": [
                                            {
                                                "type": "Column",
                                                "width": "50px",
                                                "items": [
                                                    {
                                                        "type": "TextBlock",
                                                        "text": f"#{i+1}",
                                                        "color": "accent",
                                                        "weight": "bolder",
                                                        "horizontalAlignment": "left"
                                                    }
                                                ]
                                            },
                                            {
                                                "type": "Column",
                                                "width": "100px",
                                                "items": [
                                                    {
                                                        "type": "TextBlock",
                                                        "text": f"[{issue_priority}]",
                                                        "color": PRIORITY_COLORS.get(issue_priority.lower(), "default"),
                                                        "weight": "bolder",
                                                        "horizontalAlignment": "left"
                                                    }
                                                ]
                                            },
                                            {
                                                "type": "Column",
                                                "width": "stretch",
                                                "items": [
                                                    {
                                                        "type": "TextBlock",
                                                        "text": f"{issue_name} (**{STATE_NAMES.get(issue_state, 'Inconnu')}**)",
                                                        "wrap": True,
                                                        "horizontalAlignment": "left"
                                                    }
                                                ]
                                            }
                                        ],
                                        "spacing": "medium",
                                        "selectAction": {
                                            "type": "Action.OpenUrl",
                                            "url": issue_url
                                        }
                                    }
                                    for i, (issue_priority, issue_name, issue_state, issue_url) in enumerate(self.items)
                                ]
                            }
                        ]
                    }
                }
            ]
        }

def format_issues(issues: List[PlaneIssue]) -> TeamsMessage:
    """Format a list of issues into a Teams message.
    
    Args:
        issues: List of issues to format
        
    Returns:
        TeamsMessage: The formatted message
    """
    # Filter issues by state (only keep En cours, A faire, Backlog)
    filtered_issues = [
        issue for issue in issues 
        if issue.state in STATE_ORDER.keys()
    ]
    
    # Sort by priority first, then by state
    filtered_issues.sort(key=lambda x: (
        {
            "urgent": 0,
            "high": 1,
            "medium": 2,
            "low": 3
        }.get(x.priority, 4),
        STATE_ORDER.get(x.state, 99)
    ))
    
    # Take top 10 issues
    top_issues = filtered_issues[:10]
    
    # Format issues into message items with priority colors and URLs
    items = [
        (
            issue.priority.upper(),
            issue.name,
            issue.state,
            f"https://plane.julienfroidefond.com/workspace/jfr/projects/b19ea686-c7fa-467d-92b9-1e6dcbc584b8/issues/{issue.id}"
        )
        for issue in top_issues
    ]
    
    return TeamsMessage(
        title="Top Priority Plane Issues",
        items=items
    ) 