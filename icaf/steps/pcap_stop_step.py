import os
import signal
from icaf.core.step import Step
from icaf.utils.logger import logger


class PcapStopStep(Step):

    def __init__(self):

        super().__init__("Stop packet capture")

    def execute(self, context):

        process = context.pcap_process

        if process:

            logger.info("Stopping PCAP capture")

            os.kill(process.pid, signal.SIGINT)

            context.pcap_process = None