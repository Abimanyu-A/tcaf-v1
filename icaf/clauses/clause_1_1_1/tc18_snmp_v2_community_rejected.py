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

class TC18SNMPv2CommunityRejected(TestCase):

    def __init__(self):

        super().__init__(
            "TC10_SNMPV2_COMMUNITY_ACCESS",
            "Verify SNMPv2 queries are rejected by DUT"
        )

    def run(self, context):

        snmp_cmd = context.profile.get("snmp.get_uptime_v2").format(
            community=context.snmp_community,
            ip=context.ssh_ip
        )

        try:

            StepRunner([
                PcapStartStep(interface="eth0", filename="tc10_snmpv2_test.pcapng"),
                CommandStep("tester", snmp_cmd)
            ]).run(context)

            pattern, _ = ExpectOneOfStep(
                "tester",
                ["Timeout", "No Such Object", "Timeticks"]
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

                logger.error("SNMPv2 unexpectedly succeeded")

                self.fail_test()

            else:

                logger.info("SNMPv2 correctly rejected")

                self.pass_test()

        except Exception as e:

            logger.error(str(e))

            self.fail_test()

        return self