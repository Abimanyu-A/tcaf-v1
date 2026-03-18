from icaf.core.clause import BaseClause
from .tc1_ssh_first_connection import TC1SSHFirstConnection
from .tc2_ssh_valid_credentials import TC2SSHValidCredentials
from .tc3_ssh_invalid_credentials import TC3SSHInvalidCredentials
from .tc4_https_auth_prompt import TC4HTTPSAuthPrompt
from .tc5_https_valid_credentials import TC5HTTPSValidLogin
from .tc6_https_invalid_credentials import TC6HTTPSInvalidLogin
from .tc7_ssh_v1_disabled import TC7SSHv1Disabled
from .tc8_tls10_disabled import TC8TLS10Disabled
from .tc9_tls11_disabled import TC9TLS11Disabled
from .tc11_tls_deprecated_ciphers import TC11TLSDeprecatedCiphers
from .tc12_snmp_v1_disabled import TC12SNMPv1Disabled
from .tc13_snmp_v2c_disabled import TC13SNMPv2Disabled
from .tc14_snmp_v3_authpriv import TC14SNMPv3AuthPriv
from .tc15_snmp_v3_valid_auth import TC15SNMPv3ValidAuth
from .tc16_snmp_v3_invalid_auth import TC16SNMPv3InvalidAuth
from .tc17_snmp_v3_invalid_encryption import TC17SNMPv3InvalidEncryption
from .tc18_snmp_v2_community_rejected import TC18SNMPv2CommunityRejected

class Clause_1_1_1(BaseClause):

    def __init__(self, context):

        super().__init__(context)

        self.add_testcase(TC1SSHFirstConnection())
        # self.add_testcase(TC2SSHValidCredentials())
        # self.add_testcase(TC3SSHInvalidCredentials())
        # self.add_testcase(TC4HTTPSAuthPrompt())
        # self.add_testcase(TC5HTTPSValidLogin())
        # self.add_testcase(TC6HTTPSInvalidLogin())
        # self.add_testcase(TC7SSHv1Disabled())
        # self.add_testcase(TC8TLS10Disabled())
        # self.add_testcase(TC9TLS11Disabled())
        # self.add_testcase(TC11TLSDeprecatedCiphers())
        # self.add_testcase(TC12SNMPv1Disabled())
        # self.add_testcase(TC13SNMPv2Disabled())
        # self.add_testcase(TC14SNMPv3AuthPriv())
        # self.add_testcase(TC10SNMPv3InvalidAuth())
        self.add_testcase(TC15SNMPv3ValidAuth())
        self.add_testcase(TC16SNMPv3InvalidAuth())
        self.add_testcase(TC17SNMPv3InvalidEncryption())
        self.add_testcase(TC18SNMPv2CommunityRejected())