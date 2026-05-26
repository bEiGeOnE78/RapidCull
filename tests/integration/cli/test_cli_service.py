from __future__ import annotations

import signal
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from click.testing import CliRunner

from rapidcull.cli import cli


@pytest.fixture()
def runner() -> CliRunner:
    return CliRunner()


class TestStartCommand:
    def test_start_creates_pid_file(self, runner: CliRunner, tmp_path: Path) -> None:
        """Start command writes PID to file and reports success."""
        pid_file = tmp_path / "test.pid"
        mock_proc = MagicMock()
        mock_proc.pid = 12345

        with (
            patch("rapidcull.cli._process_alive", return_value=False),
            patch("rapidcull.cli._port_in_use", return_value=False),
            patch("subprocess.Popen", return_value=mock_proc),
        ):
            result = runner.invoke(cli, ["start", "--pid-file", str(pid_file)])

        assert result.exit_code == 0
        assert pid_file.exists()
        assert pid_file.read_text().strip() == "12345"
        assert "started" in result.output.lower() or "rapidcull api" in result.output.lower()

    def test_start_already_running_error(self, runner: CliRunner, tmp_path: Path) -> None:
        """Start command errors when an existing process is alive."""
        pid_file = tmp_path / "test.pid"
        pid_file.write_text("9999\n")

        with patch("rapidcull.cli._process_alive", return_value=True):
            result = runner.invoke(cli, ["start", "--pid-file", str(pid_file)])

        assert result.exit_code != 0
        combined = (result.output + (result.stderr or "")).lower()
        assert "already running" in combined

    def test_start_port_in_use_error(self, runner: CliRunner, tmp_path: Path) -> None:
        """Start command errors when the target port is already bound."""
        pid_file = tmp_path / "test.pid"

        with (
            patch("rapidcull.cli._process_alive", return_value=False),
            patch("rapidcull.cli._port_in_use", return_value=True),
        ):
            result = runner.invoke(cli, ["start", "--pid-file", str(pid_file)])

        assert result.exit_code != 0
        combined = (result.output + (result.stderr or "")).lower()
        assert "already in use" in combined

    def test_start_stale_pid_file_is_replaced(self, runner: CliRunner, tmp_path: Path) -> None:
        """Start command succeeds and overwrites a stale PID file (dead process)."""
        pid_file = tmp_path / "test.pid"
        # Write a stale PID that the mock will report as dead
        pid_file.write_text("8888\n")

        mock_proc = MagicMock()
        mock_proc.pid = 54321

        # _process_alive is called with the stale PID and returns False
        with (
            patch("rapidcull.cli._process_alive", return_value=False),
            patch("rapidcull.cli._port_in_use", return_value=False),
            patch("subprocess.Popen", return_value=mock_proc),
        ):
            result = runner.invoke(cli, ["start", "--pid-file", str(pid_file)])

        assert result.exit_code == 0
        assert pid_file.read_text().strip() == "54321"


class TestStopCommand:
    def test_stop_removes_pid_file(self, runner: CliRunner, tmp_path: Path) -> None:
        """Stop command kills the process and removes the PID file."""
        pid_file = tmp_path / "test.pid"
        pid_file.write_text("9999\n")

        # Process is alive on first call (SIGTERM check), dead after signal
        alive_sequence = [True, False, False]

        with (
            patch("rapidcull.cli._process_alive", side_effect=alive_sequence),
            patch("os.kill") as mock_kill,
        ):
            result = runner.invoke(cli, ["stop", "--pid-file", str(pid_file)])

        assert result.exit_code == 0
        assert not pid_file.exists()
        assert "stopped" in result.output.lower()
        mock_kill.assert_any_call(9999, signal.SIGTERM)

    def test_stop_no_pid_file_error(self, runner: CliRunner, tmp_path: Path) -> None:
        """Stop command errors when no PID file exists."""
        pid_file = tmp_path / "test.pid"
        # Deliberately do not create the file

        result = runner.invoke(cli, ["stop", "--pid-file", str(pid_file)])

        assert result.exit_code != 0
        combined = (result.output + (result.stderr or "")).lower()
        assert "no running service" in combined

    def test_stop_stale_pid_cleans_up(self, runner: CliRunner, tmp_path: Path) -> None:
        """Stop command removes a stale PID file when the process is no longer alive."""
        pid_file = tmp_path / "test.pid"
        pid_file.write_text("7777\n")

        with patch("rapidcull.cli._process_alive", return_value=False):
            result = runner.invoke(cli, ["stop", "--pid-file", str(pid_file)])

        # Should succeed (return 0) and remove the file
        assert result.exit_code == 0
        assert not pid_file.exists()
        combined = (result.output + (result.stderr or "")).lower()
        assert "stale" in combined

    def test_stop_sends_sigkill_if_process_persists(
        self, runner: CliRunner, tmp_path: Path
    ) -> None:
        """Stop command escalates to SIGKILL when process does not exit after SIGTERM."""
        pid_file = tmp_path / "test.pid"
        pid_file.write_text("1111\n")

        # Always alive — triggers SIGKILL path
        with (
            patch("rapidcull.cli._process_alive", return_value=True),
            patch("os.kill") as mock_kill,
            patch("time.sleep"),  # speed up the wait loop
        ):
            result = runner.invoke(cli, ["stop", "--pid-file", str(pid_file)])

        assert result.exit_code == 0
        kill_args = [c.args for c in mock_kill.call_args_list]
        assert (1111, signal.SIGTERM) in kill_args
        assert (1111, signal.SIGKILL) in kill_args
        assert not pid_file.exists()


class TestRestartCommand:
    def test_restart_stop_then_start(self, runner: CliRunner, tmp_path: Path) -> None:
        """Restart command stops a running process and then starts a new one."""
        pid_file = tmp_path / "test.pid"
        pid_file.write_text("2222\n")

        mock_proc = MagicMock()
        mock_proc.pid = 3333

        # Sequence of _process_alive calls:
        # 1. restart reads PID (2222 exists) and checks alive → True (triggers stop)
        # 2. stop checks alive to decide between kill and stale → True
        # 3. stop loops waiting for death → False (process exited)
        # 4. stop's final "still alive?" check → False
        # 5. start checks alive on any leftover PID → False
        alive_sequence = [True, True, False, False, False]

        with (
            patch("rapidcull.cli._process_alive", side_effect=alive_sequence),
            patch("rapidcull.cli._port_in_use", return_value=False),
            patch("os.kill"),
            patch("time.sleep"),
            patch("subprocess.Popen", return_value=mock_proc),
        ):
            result = runner.invoke(
                cli,
                ["restart", "--pid-file", str(pid_file)],
            )

        assert result.exit_code == 0
        assert pid_file.exists()
        assert pid_file.read_text().strip() == "3333"

    def test_restart_no_existing_process_starts_fresh(
        self, runner: CliRunner, tmp_path: Path
    ) -> None:
        """Restart starts fresh when no existing PID file is present."""
        pid_file = tmp_path / "test.pid"
        # No PID file

        mock_proc = MagicMock()
        mock_proc.pid = 4444

        with (
            patch("rapidcull.cli._process_alive", return_value=False),
            patch("rapidcull.cli._port_in_use", return_value=False),
            patch("subprocess.Popen", return_value=mock_proc),
        ):
            result = runner.invoke(
                cli,
                ["restart", "--pid-file", str(pid_file)],
            )

        assert result.exit_code == 0
        assert pid_file.exists()
        assert pid_file.read_text().strip() == "4444"
