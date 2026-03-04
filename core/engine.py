from utils.logger import logger
from config.settings import settings
from runtime.context import RuntimeContext
from terminal.manager import TerminalManager
from device.detector import DeviceDetector
import time


class Engine:

    def __init__(self, clause=None, section=None, ssh_command=None):

        self.context = RuntimeContext(
            clause=clause,
            section=section,
            ssh_command=ssh_command
        )

        logger.info("Engine initialized")

    def start(self):

        logger.info("Starting TCAF engine")

        logger.info(f"Execution ID: {self.context.execution_id}")

        if self.context.clause:
            logger.info(f"Execution mode: Clause {self.context.clause}")

        elif self.context.section:
            logger.info(f"Execution mode: Section {self.context.section}")

        else:
            logger.info("Execution mode: Full evaluation")

        self.initialize_runtime()
        
    def initialize_runtime(self):

        logger.info("Initializing runtime environment")

        # Initialize terminal manager
        self.context.terminal_manager = TerminalManager()

        tm = self.context.terminal_manager

        # Create terminals
        tm.create_terminal("dut")
        tm.create_terminal("client")
        tm.create_terminal("monitor")
        tm.create_terminal("local")

        logger.info("Terminals created")

        # Connect DUT via SSH
        if self.context.ssh_command:
            logger.info("Connecting to DUT via SSH")

            tm.run("dut", self.context.ssh_command)
            
            time.sleep(3)
            
            detector = DeviceDetector(self.context.terminal_manager)

            device_type = detector.detect()

            self.context.device_type = device_type

            logger.info(f"DUT device type: {device_type}")

        logger.info("Runtime environment ready")