from icaf.core.testcase import TestCase
from icaf.core.step_runner import StepRunner
from icaf.steps.command_step import CommandStep
from icaf.steps.screenshot_step import ScreenshotStep


class TC11TLSDeprecatedCiphers(TestCase):

    def __init__(self):

        super().__init__(
            "TC11_TLS_DEPRECATED_CIPHERS",
            "Verify deprecated TLS ciphers are not present"
        )

    def run(self, context):

        cmd = context.profile.get("cipher_scan.scan_command").format(
            ip=context.ssh_ip
        )

        forbidden = context.profile.get("cipher_scan.deprecated_ciphers")

        StepRunner([
            CommandStep("tester", cmd)
        ]).run(context)

        tm = context.terminal_manager

        output = tm.capture_output("tester")

        for cipher in forbidden:

            if cipher in output:

                ScreenshotStep("tester").execute(context)

                self.fail_test()

                return self

        ScreenshotStep("tester").execute(context)

        self.pass_test()

        return self