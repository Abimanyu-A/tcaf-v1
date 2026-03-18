from icaf.core.step import Step
from icaf.core.step_runner import StepRunner

from icaf.steps.clear_terminal_step import ClearTerminalStep
from icaf.steps.ensure_ssh_disconnected_step import EnsureSSHDisconnectedStep
import time

class SessionResetStep(Step):

    def __init__(self, terminal):

        super().__init__("Reset session")

        self.terminal = terminal

    def execute(self, context):

        time.sleep(2)

        StepRunner([
            EnsureSSHDisconnectedStep(self.terminal),
            ClearTerminalStep(self.terminal)
        ]).run(context)

        time.sleep(3)