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


class TC15SNMPv3ValidAuth(TestCase):

    def __init__(self):

        super().__init__(
            "TC7_MUTUAL_AUTH_SNMPV3_VALID",
            "Verify SNMPv3 connection with valid authentication and encryption"
        )

    def run(self, context):
        snmp_cmd = context.profile.get("snmp.v3_valid_command").format(
            user=context.snmp_user,
            auth_pass=context.snmp_auth_pass,
            priv_pass=context.snmp_priv_pass,
            ip=context.ssh_ip
        )

        try:

            StepRunner([
                PcapStartStep(interface="eth0", filename="tc7_snmpv3_valid.pcapng"),
                CommandStep("tester", snmp_cmd)
            ]).run(context)

            pattern, _ = ExpectOneOfStep(
                "tester",
                ["Timeticks", "Timeout"]
            ).execute(context)

            StepRunner([
                PcapStopStep()
            ]).run(context)

            StepRunner([
                AnalyzePcapStep("snmp"),
                WiresharkPacketScreenshotStep()
            ]).run(context)

            ScreenshotStep("tester").execute(context)

            if pattern == "Timeticks":

                logger.info("SNMPv3 authentication successful")

                self.pass_test()

            else:

                logger.error("SNMPv3 authentication failed")

                self.fail_test()

        except Exception as e:

            logger.error(str(e))

            self.fail_test()

        return self