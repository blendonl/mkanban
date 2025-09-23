from src.core.exceptions import MKanbanError


class JiraError(MKanbanError):
    """Jira-specific error"""
    pass


class JiraAuthError(JiraError):
    """Jira authentication error"""
    pass


class JiraAPIError(JiraError):
    """Jira API error"""
    pass