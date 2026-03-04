import subprocess
import time
from utils.logger import logger
from terminal.base_terminal import BaseTerminal


class VisibleTerminal(BaseTerminal):

    def __init__(self, name: str):

        super().__init__(name)

        self.title = f"TCAF-{name}"
        self.window_id = None

        logger.info(f"Launching visible terminal: {self.title}")

        subprocess.Popen(
            [
                "gnome-terminal",
                "--title",
                self.title
            ]
        )

        time.sleep(1)

        self.window_id = self._find_window()

    def _find_window(self):

        try:
            result = subprocess.run(
                ["xdotool", "search", "--name", self.title],
                capture_output=True,
                text=True
            )

            window_id = result.stdout.strip().split("\n")[0]

            logger.info(f"{self.title} window id: {window_id}")

            return window_id

        except Exception:
            logger.error("Failed to find terminal window")
            return None

    def run(self, command: str):

        logger.info(f"[{self.name}] {command}")

        subprocess.run(
            [
                "xdotool",
                "windowactivate",
                "--sync",
                self.window_id,
                "type",
                command
            ]
        )

        subprocess.run(
            [
                "xdotool",
                "key",
                "Return"
            ]
        )

    def capture(self):

        screenshot_path = f"output/screenshots/{self.name}.png"

        logger.info(f"Capturing screenshot: {screenshot_path}")

        subprocess.run(
            [
                "scrot",
                screenshot_path
            ]
        )

        return screenshot_path