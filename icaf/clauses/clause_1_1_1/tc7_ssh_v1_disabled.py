from icaf.core.testcase import TestCase
from icaf.core.step_runner import StepRunner
from icaf.steps.command_step import CommandStep
from icaf.steps.expect_one_of_step import ExpectOneOfStep
from icaf.steps.screenshot_step import ScreenshotStep
from icaf.steps.clear_terminal_step import ClearTerminalStep


class TC7SSHv1Disabled(TestCase):

    def __init__(self):

        super().__init__(
            "TC7_SSHV1_DISABLED",
            "Verify SSH version 1 is not supported"
        )

    def run(self, context):

        ssh_cmd = context.profile.get("ssh.ssh_v1_command").format(
            user=context.ssh_user,
            ip=context.ssh_ip
        )

        password_prompts = context.profile.get("ssh.password_prompt")

        StepRunner([
            ClearTerminalStep("tester"),
            CommandStep("tester", ssh_cmd)
        ]).run(context)

        pattern, output = ExpectOneOfStep(
            "tester",
            [
                "no longer supported",
                "connection closed"
            ] + password_prompts
        ).execute(context)

        if pattern in password_prompts:

            ScreenshotStep("tester").execute(context)

            self.fail_test()

            return self

        ScreenshotStep("tester").execute(context)

        self.pass_test()

        return self