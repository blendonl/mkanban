"""Git Repository Operations

Provides high-level Git operations for branch management,
status checking, and repository introspection.
"""

import subprocess
from pathlib import Path
from typing import List, Optional, Dict, Any
from dataclasses import dataclass
from enum import Enum

from core.exceptions import MKanbanError


class BranchType(Enum):
    LOCAL = "local"
    REMOTE = "remote"
    TRACKING = "tracking"


@dataclass
class GitBranch:
    """Represents a Git branch"""
    name: str
    full_name: str
    branch_type: BranchType
    is_current: bool = False
    upstream: Optional[str] = None
    last_commit_hash: Optional[str] = None
    last_commit_message: Optional[str] = None
    last_commit_author: Optional[str] = None
    last_commit_date: Optional[str] = None


@dataclass
class GitRepository:
    """Represents a Git repository"""
    path: Path
    name: str
    current_branch: Optional[str] = None
    branches: List[GitBranch] = None
    
    def __post_init__(self):
        if self.branches is None:
            self.branches = []


class GitOperations:
    """High-level Git operations"""
    
    def __init__(self, repo_path: Path):
        self.repo_path = Path(repo_path).resolve()
        if not self.is_git_repository():
            raise MKanbanError(f"Not a git repository: {repo_path}")
    
    def is_git_repository(self) -> bool:
        """Check if the path is a git repository"""
        try:
            result = self._run_git_command(["rev-parse", "--git-dir"])
            return result.returncode == 0
        except:
            return False
    
    def get_repository_info(self) -> GitRepository:
        """Get comprehensive repository information"""
        repo_name = self.repo_path.name
        current_branch = self.get_current_branch()
        branches = self.get_all_branches()
        
        return GitRepository(
            path=self.repo_path,
            name=repo_name,
            current_branch=current_branch,
            branches=branches
        )
    
    def get_current_branch(self) -> Optional[str]:
        """Get the currently checked out branch"""
        try:
            result = self._run_git_command(["rev-parse", "--abbrev-ref", "HEAD"])
            if result.returncode == 0:
                branch_name = result.stdout.strip()
                return branch_name if branch_name != "HEAD" else None
            return None
        except:
            return None
    
    def get_all_branches(self) -> List[GitBranch]:
        """Get all branches in the repository"""
        branches = []
        current_branch = self.get_current_branch()
        
        # Get local branches
        try:
            result = self._run_git_command(["branch", "-v", "--no-abbrev"])
            if result.returncode == 0:
                for line in result.stdout.split('\n'):
                    if line.strip():
                        branch = self._parse_branch_line(line, BranchType.LOCAL, current_branch)
                        if branch:
                            branches.append(branch)
        except:
            pass
        
        # Get remote branches
        try:
            result = self._run_git_command(["branch", "-r", "-v", "--no-abbrev"])
            if result.returncode == 0:
                for line in result.stdout.split('\n'):
                    if line.strip() and "HEAD ->" not in line:
                        branch = self._parse_branch_line(line, BranchType.REMOTE, current_branch)
                        if branch:
                            branches.append(branch)
        except:
            pass
        
        return branches
    
    def get_local_branches(self) -> List[str]:
        """Get list of local branch names"""
        try:
            result = self._run_git_command(["branch", "--format=%(refname:short)"])
            if result.returncode == 0:
                return [line.strip() for line in result.stdout.split('\n') if line.strip()]
            return []
        except:
            return []
    
    def branch_exists(self, branch_name: str) -> bool:
        """Check if a branch exists"""
        try:
            result = self._run_git_command(["rev-parse", "--verify", f"refs/heads/{branch_name}"])
            return result.returncode == 0
        except:
            return False
    
    def get_branch_info(self, branch_name: str) -> Optional[GitBranch]:
        """Get detailed information about a specific branch"""
        if not self.branch_exists(branch_name):
            return None
        
        try:
            # Get commit info
            commit_info = self._run_git_command([
                "log", "-1", "--format=%H|%s|%an|%ad", "--date=iso", branch_name
            ])
            
            if commit_info.returncode == 0:
                parts = commit_info.stdout.strip().split('|', 3)
                if len(parts) == 4:
                    hash_val, message, author, date = parts
                    
                    return GitBranch(
                        name=branch_name,
                        full_name=f"refs/heads/{branch_name}",
                        branch_type=BranchType.LOCAL,
                        is_current=(branch_name == self.get_current_branch()),
                        last_commit_hash=hash_val,
                        last_commit_message=message,
                        last_commit_author=author,
                        last_commit_date=date
                    )
        except:
            pass
        
        return GitBranch(
            name=branch_name,
            full_name=f"refs/heads/{branch_name}",
            branch_type=BranchType.LOCAL,
            is_current=(branch_name == self.get_current_branch())
        )
    
    def _parse_branch_line(self, line: str, branch_type: BranchType, current_branch: Optional[str]) -> Optional[GitBranch]:
        """Parse a line from git branch output"""
        line = line.strip()
        if not line:
            return None
        
        # Remove current branch indicator
        is_current = line.startswith('*')
        if is_current:
            line = line[1:].strip()
        
        parts = line.split()
        if len(parts) < 2:
            return None
        
        branch_name = parts[0]
        commit_hash = parts[1]
        
        # Extract commit message
        commit_message = ' '.join(parts[2:]) if len(parts) > 2 else ""
        
        # For remote branches, clean up the name
        if branch_type == BranchType.REMOTE:
            if '/' in branch_name:
                # Remove remote prefix (e.g., "origin/feature-branch" -> "feature-branch")
                branch_name = branch_name.split('/', 1)[1]
        
        full_name = f"refs/heads/{branch_name}" if branch_type == BranchType.LOCAL else f"refs/remotes/{parts[0]}"
        
        return GitBranch(
            name=branch_name,
            full_name=full_name,
            branch_type=branch_type,
            is_current=is_current or (branch_name == current_branch),
            last_commit_hash=commit_hash,
            last_commit_message=commit_message
        )
    
    def _run_git_command(self, args: List[str]) -> subprocess.CompletedProcess:
        """Run a git command in the repository directory"""
        cmd = ["git"] + args
        return subprocess.run(
            cmd,
            cwd=self.repo_path,
            capture_output=True,
            text=True,
            timeout=30
        )


def find_git_repositories(search_path: Path, max_depth: int = 3) -> List[Path]:
    """Find all git repositories under the given path"""
    repositories = []
    
    def _search_recursive(path: Path, depth: int):
        if depth > max_depth:
            return
        
        try:
            if (path / ".git").exists():
                repositories.append(path)
                return  # Don't search inside git repos
            
            if path.is_dir():
                for item in path.iterdir():
                    if item.is_dir() and not item.name.startswith('.'):
                        _search_recursive(item, depth + 1)
        except (PermissionError, OSError):
            pass
    
    _search_recursive(search_path, 0)
    return repositories