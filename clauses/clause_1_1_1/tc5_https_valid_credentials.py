from core.testcase import TestCase
from core.step_runner import StepRunner
from steps.open_url_step import OpenURLStep
from steps.browser_screenshot_step import BrowserScreenshotStep
from steps.auto_login_step import AutoLoginStep


class TC5HTTPSValidLogin(TestCase):

    def __init__(self):

        super().__init__(
            "TC5_HTTPS_VALID_LOGIN",
            "Valid HTTPS credentials should allow login"
        )

    def run(self, context):

        login_path = context.profile.get("https.login_path")

        url = f"http://{context.ssh_ip}{login_path}"

        StepRunner([
            OpenURLStep(url),
            AutoLoginStep(),
            BrowserScreenshotStep("https_valid_login.png")
        ]).run(context)

        self.pass_test()

        return self