from icaf.core.testcase import TestCase
from icaf.core.step_runner import StepRunner

from icaf.steps.command_step import CommandStep
from icaf.steps.expect_one_of_step import ExpectOneOfStep
from icaf.steps.screenshot_step import ScreenshotStep
from icaf.steps.input_step import InputStep
from icaf.steps.pcap_start_step import PcapStartStep
from icaf.steps.pcap_stop_step import PcapStopStep
from icaf.steps.analyze_pcap_step import AnalyzePcapStep
from icaf.steps.wireshark_packet_screenshot_step import WiresharkPacketScreenshotStep
from icaf.steps.session_reset_step import SessionResetStep
from icaf.steps.clear_terminal_step import ClearTerminalStep

from icaf.utils.logger import logger


class TC1SSHFirstConnection(TestCase):

    def __init__(self):

        super().__init__(
            "TC1_MUTUAL_AUTHENTICATION",
            "SSH first connection mutual authentication"
        )

    def run(self, context):

        ssh_cmd = context.profile.get("ssh.connect_command").format(
            user=context.ssh_user,
            ip=context.ssh_ip
        )

        fingerprint_prompts = context.profile.get("ssh.fingerprint_prompt")
        password_prompts = context.profile.get("ssh.password_prompt")
        failure_prompts = context.profile.get("ssh.failure_prompt")

        StepRunner([
            PcapStartStep(interface="eth0", filename="tc1_ssh_auth.pcapng"),
            CommandStep("tester", ssh_cmd)
        ]).run(context)

        pattern, _ = ExpectOneOfStep(
            "tester",
            fingerprint_prompts
            + password_prompts
            + failure_prompts
            + ["Network is unreachable"]
        ).execute(context)

        if pattern in fingerprint_prompts:

            logger.info("SSH fingerprint prompt detected")

            StepRunner([
                InputStep("tester", "yes")
            ]).run(context)

            pattern, _ = ExpectOneOfStep(
                "tester",
                password_prompts
            ).execute(context)

        if pattern in password_prompts:

            logger.info("Password prompt detected")

            StepRunner([
                InputStep("tester", context.ssh_password),
                PcapStopStep()
            ]).run(context)

            StepRunner([
                AnalyzePcapStep("ssh"),
                WiresharkPacketScreenshotStep()
            ]).run(context)

            ScreenshotStep("tester").execute(context)

            StepRunner([
                SessionResetStep("tester")
            ]).run(context)

            self.pass_test()

            return self

        if pattern in failure_prompts:

            logger.error("SSH connection failed")

            ScreenshotStep("tester").execute(context)

            self.fail_test()

            return self

        if pattern == "Network is unreachable":

            logger.error("Network unreachable")

            StepRunner([
                PcapStopStep()
            ]).run(context)

            ScreenshotStep("tester").execute(context)

            StepRunner([
                ClearTerminalStep("tester")
            ]).run(context)

            self.fail_test()

            return self