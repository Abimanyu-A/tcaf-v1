import uuid
from datetime import datetime


class RuntimeContext:
    """
    Shared runtime state used across the TCAF framework.
    """

    def __init__(self, clause=None, section=None):

        self.execution_id = str(uuid.uuid4())

        self.start_time = datetime.utcnow()

        # CLI parameters
        self.clause = clause
        self.section = section

        # Core subsystems (initialized later)
        self.ssh_connection = None
        self.terminal_manager = None

        # Device information
        self.device_type = None
        self.device_info = {}

        # Adapter
        self.adapter = None

        # Evidence tracking
        self.evidence = []

    def summary(self):
        """
        Return basic execution summary.
        """

        return {
            "execution_id": self.execution_id,
            "clause": self.clause,
            "section": self.section,
            "device_type": self.device_type,
            "start_time": str(self.start_time),
        }