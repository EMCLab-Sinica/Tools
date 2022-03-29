import logging
import platform
import os
import subprocess
from subprocess import PIPE

import uart_utils

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('minicom-launcher')

def check_minicom():
    try:
        minicom_version_raw = subprocess.run(["minicom", "-v"], check=False, stdout=PIPE).stdout
    except FileNotFoundError:
        print("Minicom is not installed")
        exit(1)

    minicom_version = minicom_version_raw.split()[2].decode()
    return minicom_version

def open_minicom(device, baudrate):
    cmd = ["minicom", f"--device={device}", "--baudrate", f"{baudrate}"]
    if platform.system() == "Darwin":
        cmd.append("-m")
    env = os.environ.copy()
    env['LC_MESSAGES'] = 'en_US.UTF-8'
    subprocess.run(cmd, env=env)


def baudrate(target_dev):
    if 'Cypress' in target_dev:
        return 115200
    else:
        return 9600

def run_minicom(device_list: list):

    minicom_version = check_minicom()

    print(f"MSP430 Minicom Connector (minicom version {minicom_version})\n")
    print("Found {} MSP430 UART Terminal(s)".format(len(device_list)))
    for index, device in enumerate(device_list):
        print(f"{index}\t{device}")

    if len(device_list) > 1:
        dev_num = input("Device to connect {}: ".format([n for n in range(len(device_list))]))

        try:
            dev_num = int(dev_num)
        except ValueError:
            print("Exit")
            exit(0)
    elif len(device_list) == 1:
        dev_num = 0
    else:
        print("No devices found")
        exit(0)

    try:
        target_dev = device_list[dev_num]
    except IndexError as e:
        print(e)
        exit(1)

    open_minicom(target_dev, baudrate(target_dev))

if __name__ == "__main__":
    uart_devices = uart_utils.find_uart()
    run_minicom(uart_devices)
