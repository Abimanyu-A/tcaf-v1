from icaf.core.testcase import TestCase
from icaf.core.step_runner import StepRunner

from icaf.steps.command_step import CommandStep
from icaf.steps.expect_one_of_step import ExpectOneOfStep
from icaf.steps.screenshot_step import ScreenshotStep
from icaf.steps.pcap_start_step import PcapStartStep
from icaf.steps.pcap_stop_step import PcapStopStep
from icaf.steps.analyze_pcap_step import AnalyzePcapStep
from icaf.steps.wireshark_packet_screenshot_step import WiresharkPacketScreenshotStep

from icaf.utils.logger import logger


class TC17SNMPv3InvalidEncryption(TestCase):

    def __init__(self):

        super().__init__(
            "TC9_MUTUAL_AUTH_SNMPV3_INVALID_ENCRYPTION",
            "Verify SNMPv3 connection with incorrect encryption password"
        )

    def run(self, context):

        snmp_cmd = context.profile.get("snmp.v3_wrong_priv_command").format(
            user=context.snmp_user,
            auth_pass=context.snmp_auth_pass,
            wrong_priv="wrongprivpass",
            ip=context.ssh_ip
        )

        try:

            StepRunner([
                PcapStartStep(interface="eth0", filename="tc9_snmpv3_invalid_priv.pcapng"),
                CommandStep("tester", snmp_cmd)
            ]).run(context)

            pattern, _ = ExpectOneOfStep(
                "tester",
                ["Timeout", "decryption"]
            ).execute(context)

            StepRunner([
                PcapStopStep()
            ]).run(context)

            StepRunner([
                AnalyzePcapStep("snmp"),
                WiresharkPacketScreenshotStep()
            ]).run(context)

            ScreenshotStep("tester").execute(context)

            logger.info("SNMPv3 encryption validation completed")

            self.pass_test()

        except Exception as e:

            logger.error(str(e))

            self.fail_test()

        return self