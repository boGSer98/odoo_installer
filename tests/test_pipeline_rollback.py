import unittest
from unittest import mock

from odoo_installer.models import InstallerConfig
from odoo_installer.pipeline import Step, run_installation
from odoo_installer.ssh import CommandResult


class _FakeExecutor:
    def __init__(self, fail_on: set[str]) -> None:
        self.fail_on = fail_on
        self.commands: list[str] = []

    def run(self, local_command: str) -> CommandResult:
        self.commands.append(local_command)
        if local_command in self.fail_on:
            return CommandResult(command=[local_command], returncode=1, stdout="", stderr="boom")
        return CommandResult(command=[local_command], returncode=0, stdout="", stderr="")


class _FakeProgress:
    def __init__(self) -> None:
        self.completed: list[tuple[int, int]] = []
        self.cleared = False

    def should_skip(self, step_index: int, command_index: int) -> bool:
        return False

    def mark_done(self, step_index: int, command_index: int) -> None:
        self.completed.append((step_index, command_index))

    def clear(self) -> None:
        self.cleared = True


def _config() -> InstallerConfig:
    return InstallerConfig(
        db_password="secret-db",
        admin_password="secret-admin",
    )


class PipelineRollbackTests(unittest.TestCase):
    @mock.patch("odoo_installer.pipeline.run_preflight", return_value=[])
    @mock.patch(
        "odoo_installer.pipeline.build_steps",
        return_value=[
            Step(name="Step 1", commands=["ok-1"], rollback_commands=["rb-1"]),
            Step(name="Step 2", commands=["fail-2"], rollback_commands=["rb-2"]),
        ],
    )
    def test_rollback_runs_in_reverse_order_on_failure(self, _build_steps: mock.Mock, _preflight: mock.Mock) -> None:
        executor = _FakeExecutor(fail_on={"fail-2"})
        progress = _FakeProgress()

        with self.assertRaises(RuntimeError) as ctx:
            run_installation(executor, _config(), progress=progress, rollback_on_fail=True)

        self.assertIn("Rollback ausgefuehrt", str(ctx.exception))
        self.assertEqual(executor.commands, ["ok-1", "fail-2", "rb-2", "rb-1"])
        self.assertTrue(progress.cleared)

    @mock.patch("odoo_installer.pipeline.run_preflight", return_value=[])
    @mock.patch(
        "odoo_installer.pipeline.build_steps",
        return_value=[
            Step(name="Step 1", commands=["ok-1"], rollback_commands=["rb-1"]),
            Step(name="Step 2", commands=["fail-2"], rollback_commands=["rb-2"]),
        ],
    )
    def test_failure_without_rollback_keeps_progress_state(self, _build_steps: mock.Mock, _preflight: mock.Mock) -> None:
        executor = _FakeExecutor(fail_on={"fail-2"})
        progress = _FakeProgress()

        with self.assertRaises(RuntimeError) as ctx:
            run_installation(executor, _config(), progress=progress, rollback_on_fail=False)

        self.assertNotIn("Rollback ausgefuehrt", str(ctx.exception))
        self.assertEqual(executor.commands, ["ok-1", "fail-2"])
        self.assertFalse(progress.cleared)


if __name__ == "__main__":
    unittest.main()
