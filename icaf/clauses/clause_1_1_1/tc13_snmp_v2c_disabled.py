from icaf.core.testcase import TestCase
from icaf.core.step_runner import StepRunner
from icaf.steps.command_step import CommandStep
from icaf.steps.screenshot_step import ScreenshotStep
from icaf.steps.clear_terminal_step import ClearTerminalStep


class TC13SNMPv2Disabled(TestCase):

    def __init__(self):

        super().__init__(
            "TC8_SNMPV2_DISABLED",
            "Verify SNMPv2c is not supported"
        )

    def run(self, context):

        cmd = context.profile.get("snmp.v2_command").format(
            ip=context.ssh_ip
        )

        failure_indicators = context.profile.get("snmp.failure_indicators")

        tm = context.terminal_manager

        StepRunner([
            ClearTerminalStep("dut"),
            CommandStep("dut", cmd)
        ]).run(context)

        output = tm.capture_output("dut")

        if any(indicator in output for indicator in failure_indicators):

            ScreenshotStep("dut").execute(context)

            self.pass_test()

            return self

        ScreenshotStep("dut").execute(context)

        self.fail_test()

        return self