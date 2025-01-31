"""
Teams message formatter for Plane issues.
"""
from dataclasses import dataclass
from typing import Dict, List, Tuple

from plane_to_teams.plane_client import PlaneIssue, PlaneState

PRIORITY_COLORS = {
    "urgent": "ff0000",  # Red
    "high": "ffa500",    # Orange
    "medium": "008000",  # Green
    "low": "0000ff"      # Blue
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
            color = PRIORITY_COLORS.get(priority.lower(), "000000")
            
            facts.append({
                "name": f"#{i+1}",
                "value": f"<span style='color:#{color}'>[{priority}]</span> [{name}]({url}) - **{state}**"
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


def format_issues(issues: List[PlaneIssue], states: List[PlaneState]) -> TeamsMessage:
    """Format a list of issues into a Teams message.
    
    Args:
        issues: List of issues to format
        states: List of states from Plane API
        
    Returns:
        TeamsMessage: The formatted message
    """
    # Create a map of state IDs to state objects
    state_map = {state.id: state for state in states}
    
    # Filter issues by state group (only keep backlog, unstarted, started)
    filtered_issues = [
        issue for issue in issues 
        if state_map[issue.state].group in ['backlog', 'unstarted', 'started']
    ]
    
    # Sort by priority first, then by state sequence
    filtered_issues.sort(key=lambda x: (
        {
            "urgent": 0,
            "high": 1,
            "medium": 2,
            "low": 3
        }.get(x.priority, 4),
        state_map[x.state].sequence
    ))
    
    # Take top 10 issues
    top_issues = filtered_issues[:10]
    
    # Format issues into message items with priority colors and URLs
    items = [
        (
            issue.priority.upper(),
            issue.name,
            state_map[issue.state].name,
            f"https://plane.julienfroidefond.com/workspace/jfr/projects/b19ea686-c7fa-467d-92b9-1e6dcbc584b8/issues/{issue.id}"
        )
        for issue in top_issues
    ]
    
    return TeamsMessage(
        title="Top Priority Plane Issues",
        items=items
    ) 