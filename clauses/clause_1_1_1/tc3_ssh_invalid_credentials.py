from core.testcase import TestCase
from core.step_runner import StepRunner

from steps.command_step import CommandStep
from steps.expect_one_of_step import ExpectOneOfStep
from steps.screenshot_step import ScreenshotStep
from steps.input_step import InputStep
from steps.session_reset_step import SessionResetStep
from steps.clear_terminal_step import ClearTerminalStep

from utils.logger import logger


class TC3SSHInvalidCredentials(TestCase):

    def __init__(self):

        super().__init__(
            "TC3_SSH_INVALID_CREDENTIALS",
            "Tester should not connect with invalid SSH credentials"
        )

    def run(self, context):

        ssh_cmd = context.profile.get("ssh.connect_command").format(
            user=context.ssh_user,
            ip=context.ssh_ip
        )

        fingerprint_prompts = context.profile.get("ssh.fingerprint_prompt")
        password_prompts = context.profile.get("ssh.password_prompt")
        success_prompts = context.profile.get("ssh.success_prompt")
        failure_prompts = context.profile.get("ssh.failure_prompt")

        invalid_password = context.profile.get(
            "ssh.invalid_password",
            "wrongpassword"
        )

        try:

            StepRunner([
                CommandStep("tester", ssh_cmd)
            ]).run(context)

            pattern, _ = ExpectOneOfStep(
                "tester",
                password_prompts + fingerprint_prompts + failure_prompts
            ).execute(context)

            if pattern in fingerprint_prompts:

                StepRunner([
                    InputStep("tester", "yes")
                ]).run(context)

                pattern, _ = ExpectOneOfStep(
                    "tester",
                    password_prompts
                ).execute(context)

            if pattern in failure_prompts:

                logger.error("SSH connection refused")

                ScreenshotStep("tester").execute(context)

                self.fail_test()

                return self

            for _ in range(3):

                StepRunner([
                    InputStep("tester", invalid_password)
                ]).run(context)

                pattern, _ = ExpectOneOfStep(
                    "tester",
                    failure_prompts + password_prompts + success_prompts + ["Connection closed"]
                ).execute(context)

                if pattern in success_prompts:

                    logger.error("SSH login succeeded with invalid credentials")

                    ScreenshotStep("tester").execute(context)

                    self.fail_test()

                    return self

                if pattern == "Connection closed":

                    break

            ScreenshotStep("tester").execute(context)

            logger.info("Invalid SSH credentials rejected")

            self.pass_test()

        finally:

            StepRunner([
                ClearTerminalStep("tester")
            ]).run(context)

        return self