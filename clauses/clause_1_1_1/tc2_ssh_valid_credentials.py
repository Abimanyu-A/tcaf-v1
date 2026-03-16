from core.testcase import TestCase
from core.step_runner import StepRunner

from steps.command_step import CommandStep
from steps.expect_one_of_step import ExpectOneOfStep
from steps.screenshot_step import ScreenshotStep
from steps.input_step import InputStep
from steps.session_reset_step import SessionResetStep

from utils.logger import logger


class TC2SSHValidCredentials(TestCase):

    def __init__(self):

        super().__init__(
            "TC2_SSH_VALID_CREDENTIALS",
            "Tester connects to DUT via SSH with valid credentials"
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

        verify_cmd = context.profile.get("ssh.commands.verify_login")
        print(verify_cmd)

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

            StepRunner([
                InputStep("tester", context.ssh_password)
            ]).run(context)

            pattern, _ = ExpectOneOfStep(
                "tester",
                success_prompts + failure_prompts
            ).execute(context)

            if pattern in failure_prompts:

                logger.error("Valid SSH credentials rejected")

                ScreenshotStep("tester").execute(context)

                self.fail_test()

                return self

            StepRunner([
                CommandStep("tester", verify_cmd)
            ]).run(context)

            ExpectOneOfStep(
                "tester",
                [context.ssh_user]
            ).execute(context)

            ScreenshotStep("tester").execute(context)

            logger.info("SSH login verified")

            self.pass_test()

        finally:

            StepRunner([
                SessionResetStep("tester")
            ]).run(context)

        return self