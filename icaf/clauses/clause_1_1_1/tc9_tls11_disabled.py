from icaf.core.testcase import TestCase
from icaf.core.step_runner import StepRunner
from icaf.steps.command_step import CommandStep
from icaf.steps.expect_one_of_step import ExpectOneOfStep
from icaf.steps.screenshot_step import ScreenshotStep


class TC9TLS11Disabled(TestCase):

    def __init__(self):

        super().__init__(
            "TC9_TLS11_DISABLED",
            "Verify TLS 1.1 is disabled"
        )

    def run(self, context):

        cmd = context.profile.get("tls.tls11_test_command").format(
            ip=context.ssh_ip
        )

        failure_indicators = context.profile.get("tls.failure_indicators")
        success_indicator = context.profile.get("tls.success_indicator")

        StepRunner([
            CommandStep("tester", cmd)
        ]).run(context)

        pattern, output = ExpectOneOfStep(
            "tester",
            failure_indicators + [success_indicator]
        ).execute(context)

        if pattern == success_indicator:

            ScreenshotStep("tester").execute(context)

            self.fail_test()

            return self

        ScreenshotStep("tester").execute(context)

        self.pass_test()

        return self