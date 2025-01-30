"""
Teams message formatter for Plane issues.
"""
from dataclasses import dataclass
from typing import Dict, List, Tuple

from plane_to_teams.plane_client import PlaneIssue

PRIORITY_COLORS = {
    "urgent": "ff0000",  # Red
    "high": "ffa500",    # Orange
    "medium": "008000",  # Green
    "low": "0000ff"      # Blue
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
        facts = []
        for i, (priority, name, state, url) in enumerate(self.items):
            state_name = STATE_NAMES.get(state, "Unknown")
            color = PRIORITY_COLORS.get(priority.lower(), "000000")
            
            facts.append({
                "name": f"#{i+1}",
                "value": f"<span style='color:#{color}'>[{priority}]</span> [{name}]({url}) - **{state_name}**"
            })

        return {
            "@type": "MessageCard",
            "@context": "http://schema.org/extensions",
            "themeColor": "0076D7",
            "summary": self.title,
            "title": "🎯 " + self.title,
            "sections": [{
                "facts": facts,
                "markdown": True
            }]
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