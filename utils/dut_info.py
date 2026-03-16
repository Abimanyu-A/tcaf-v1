import subprocess

def ssh_cmd(user, ip, password, cmd):

    result = subprocess.run(
        [
            "sshpass",
            "-p", password,
            "ssh",
            "-o", "HostKeyAlgorithms=+ssh-rsa",
            "-o", "PubkeyAcceptedAlgorithms=+ssh-rsa",
            "-o", "StrictHostKeyChecking=no",
            f"{user}@{ip}",
            cmd
        ],
        capture_output=True,
        text=True
    )

    return result.stdout.strip() or "Unknown"


def get_dut_info(user, ip, password):

    hostname = ssh_cmd(user, ip, password, "hostname")

    # -------- OS VERSION --------
    os_release = ssh_cmd(user, ip, password, "cat /etc/os-release")

    version = "Unknown"

    for line in os_release.splitlines():

        if line.startswith("PRETTY_NAME="):

            version = line.split("=", 1)[1].strip().strip('"')

            break

    # -------- OS HASH --------
    os_hash = ssh_cmd(
        user,
        ip,
        password,
        "sha256sum /etc/os-release 2>/dev/null | awk '{print $1}'"
    )

    # -------- CONFIG HASH --------
    config_hash = ssh_cmd(
        user,
        ip,
        password,
        "sha256sum /etc/ssh/sshd_config 2>/dev/null | awk '{print $1}'"
    )

    return {
        "dut_name": hostname if hostname else "Unknown",
        "dut_version": version,
        "os_hash": os_hash,
        "config_hash": config_hash
    }