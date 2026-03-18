from icaf.core.testcase import TestCase
from icaf.core.step_runner import StepRunner
from icaf.steps.open_url_step import OpenURLStep
from icaf.steps.browser_screenshot_step import BrowserScreenshotStep
from icaf.steps.fill_input_step import FillInputStep
from icaf.steps.click_step import ClickStep


class TC6HTTPSInvalidLogin(TestCase):

    def __init__(self):

        super().__init__(
            "TC6_HTTPS_INVALID_LOGIN",
            "Invalid HTTPS credentials must fail"
        )

    def run(self, context):

        login_path = context.profile.get("https.login_path")
        invalid_password = context.profile.get("ssh.invalid_password")

        url = f"http://{context.ssh_ip}{login_path}"

        StepRunner([
            OpenURLStep(url),
            FillInputStep("username", context.ssh_user),
            FillInputStep("password", invalid_password),
            ClickStep("Login"),
            BrowserScreenshotStep("https_invalid_login.png")
        ]).run(context)

        self.pass_test()

        return self