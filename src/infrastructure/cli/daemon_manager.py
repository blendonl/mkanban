"""Daemon Manager for CLI

Handles daemon management commands like start, stop, status, and restart
through the CLI interface.
"""

import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Optional

import click
from src.core.constants import DAEMON_STARTUP_WAIT

from src.infrastructure.tmux.session_manager import (
    get_mkanban_data_path,
    TmuxSessionManager,
)


class DaemonManager:
    """Manages the MKanban daemon through CLI commands"""

    def __init__(self, session_name: Optional[str] = None):
        self.daemon_script = self._find_daemon_script()

        # Use global data path - session isolation happens via board names
        self.data_path = get_mkanban_data_path()

        # Store session name for potential future use
        if session_name:
            self.session_name = session_name
        else:
            # Auto-detect current tmux session
            tmux_manager = TmuxSessionManager()
            current_session = tmux_manager.get_current_session()
            self.session_name = current_session.name if current_session else None

        self.pid_file = self.data_path / "daemon.pid"

    def _find_daemon_script(self) -> Optional[Path]:
        """Find the daemon script in various locations"""
        # Check local development script first
        script_path = (
            Path(__file__).parent.parent.parent / "scripts" / "mkanban_daemon.py"
        )
        if script_path.exists():
            return script_path

        # Check if mkanban-daemon is in PATH (fallback)
        try:
            result = subprocess.run(
                ["which", "mkanban-daemon"], capture_output=True, text=True
            )
            if result.returncode == 0:
                return Path(result.stdout.strip())
        except:
            pass

        return None

    def handle_daemon_command(self, command: str) -> None:
        """Handle a daemon management command"""
        if command == "start":
            self.start_daemon()
        elif command == "stop":
            self.stop_daemon()
        elif command == "status":
            self.show_status()
        elif command == "restart":
            self.restart_daemon()
        else:
            click.echo(f"Unknown daemon command: {command}")
            sys.exit(1)

    def start_daemon(self) -> None:
        """Start the daemon"""
        if self.is_daemon_running():
            click.echo("Daemon is already running")
            return

        if not self.daemon_script:
            click.echo("Error: Could not find mkanban-daemon script")
            click.echo("Please ensure it's installed or run from the project directory")
            sys.exit(1)

        try:
            # Find the project root directory (containing main.py)
            project_root = Path(__file__).parent.parent.parent.parent

            # Set environment with Python path to include project root
            env = dict(os.environ)
            current_pythonpath = env.get('PYTHONPATH', '')
            if current_pythonpath:
                env['PYTHONPATH'] = f"{project_root}:{current_pythonpath}"
            else:
                env['PYTHONPATH'] = str(project_root)

            # Start daemon as background process with temporary stderr capture for debugging
            log_file = self.data_path / "logs" / "daemon_startup.log"
            log_file.parent.mkdir(parents=True, exist_ok=True)

            with open(log_file, 'w') as f:
                # Run as a module to avoid import path issues
                process = subprocess.Popen(
                    [sys.executable, "-m", "src.scripts.mkanban_daemon"],
                    stdout=f,
                    stderr=subprocess.STDOUT,
                    start_new_session=True,
                    env=env,
                    cwd=str(project_root),
                )

            # Give it a moment to start and create its own PID file
            time.sleep(DAEMON_STARTUP_WAIT)

            if self.is_daemon_running():
                pid = self.get_daemon_pid()
                click.echo(f"Daemon started successfully (PID: {pid})")
                click.echo(f"Data directory: {self.data_path}")
            else:
                click.echo("Error: Daemon failed to start")
                sys.exit(1)

        except Exception as e:
            click.echo(f"Error starting daemon: {e}")
            sys.exit(1)

    def stop_daemon(self) -> None:
        """Stop the daemon"""
        if not self.is_daemon_running():
            click.echo("Daemon is not running")
            return

        try:
            pid = self.get_daemon_pid()
            if pid:
                # Try graceful shutdown first
                subprocess.run(["kill", "-TERM", str(pid)], timeout=5)

                # Wait for graceful shutdown
                for _ in range(10):
                    if not self.is_daemon_running():
                        break
                    time.sleep(0.5)

                # Force kill if still running
                if self.is_daemon_running():
                    subprocess.run(["kill", "-KILL", str(pid)])
                    time.sleep(1)

                # Clean up PID file
                if self.pid_file.exists():
                    self.pid_file.unlink()

                if not self.is_daemon_running():
                    click.echo("Daemon stopped successfully")
                else:
                    click.echo("Error: Could not stop daemon")
                    sys.exit(1)
            else:
                click.echo("Error: Could not find daemon PID")

        except Exception as e:
            click.echo(f"Error stopping daemon: {e}")
            sys.exit(1)

    def restart_daemon(self) -> None:
        """Restart the daemon"""
        if self.is_daemon_running():
            click.echo("Stopping daemon...")
            self.stop_daemon()

        click.echo("Starting daemon...")
        self.start_daemon()

    def show_status(self) -> None:
        """Show daemon status"""
        if self.is_daemon_running():
            pid = self.get_daemon_pid()
            click.echo(f"Daemon is running (PID: {pid})")
            click.echo(f"Data directory: {self.data_path}")

            # Show additional info if possible
            self._show_daemon_info()
        else:
            click.echo("Daemon is not running")
            if self.pid_file.exists():
                click.echo("(Stale PID file found - daemon may have crashed)")

    def is_daemon_running(self) -> bool:
        """Check if the daemon is currently running"""
        pid = self.get_daemon_pid()
        if not pid:
            return False

        try:
            # Check if process exists
            subprocess.run(["kill", "-0", str(pid)], check=True, capture_output=True)
            return True
        except subprocess.CalledProcessError:
            # Process doesn't exist, clean up stale PID file
            if self.pid_file.exists():
                self.pid_file.unlink()
            return False

    def get_daemon_pid(self) -> Optional[int]:
        """Get the daemon PID from the PID file"""
        if not self.pid_file.exists():
            return None

        try:
            return int(self.pid_file.read_text().strip())
        except (ValueError, OSError):
            return None

    def _show_daemon_info(self) -> None:
        """Show additional daemon information"""
        try:
            # Check if we're in a tmux session
            from ...infrastructure.tmux.session_manager import TmuxSessionManager

            tmux_manager = TmuxSessionManager()

            if tmux_manager.is_in_tmux_session():
                session = tmux_manager.get_current_session()
                repo = tmux_manager.get_active_session_repository()

                if session:
                    click.echo(f"Current tmux session: {session.name}")
                if repo:
                    click.echo(f"Monitoring repository: {repo}")
                else:
                    click.echo("No git repository in current tmux session")
            else:
                click.echo("Not in a tmux session")

            # Check for log file
            log_file = self.data_path / "logs" / "daemon.log"
            if log_file.exists():
                click.echo(f"Log file: {log_file}")

        except Exception:
            # Don't fail if we can't get additional info
            pass
