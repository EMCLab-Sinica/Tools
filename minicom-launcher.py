import platform
import os
import re
import subprocess
from subprocess import PIPE

current_os = platform.system()

def find_430_macOS():
    """
    Find MSP430 device path
        args: None
        return: [path_to_dev]
    """
    DEVICE_PATH = "/dev"
    devices = os.listdir(DEVICE_PATH)
    usb_devices = [dev for dev in devices if dev.startswith("tty.usbmodem")]
    usb_devices.sort()
    msp430_uart_terminals = [os.path.join(DEVICE_PATH, dev)
                             for dev in usb_devices if dev.endswith("03")]

    return msp430_uart_terminals

def find_430_Linux():
    print("Linux is not yet supported :(")
    return []

def check_minicom():
    try:
        minicom_version_raw = subprocess.run(["minicom", "-v"], check=False, stdout=PIPE).stdout
    except FileNotFoundError:
        print("Minicom is not installed")
        exit(1)

    minicom_version = minicom_version_raw.split()[2].decode()
    return minicom_version

def open_minicom(device, baudrate):
    subprocess.run(["minicom", f"--device={device}", "--baudrate", f"{baudrate}", "-m"])

def shell(device_list: list):

    minicom_version = check_minicom()

    print(f"EMCLab MSP430 Minicom Connector (minicom version {minicom_version})\n")
    print("Found {} MSP430 UART Terminal(s)".format(len(device_list)))
    for index, device in enumerate(device_list):
        print(f"{index}\t{device}")
    dev_num = input("Device to connect {}: ".format([n for n in range(len(device_list))]))

    try:
        dev_num = int(dev_num)
    except ValueError as e:
        print("Exit")
        exit(0)

    try:
        target_dev = device_list[dev_num]
    except IndexError as e:
        print(e)
        exit(1)

    open_minicom(target_dev, 9600)

if __name__ == "__main__":
    msp430_devices = []
    if current_os == "Darwin": # macOS
        msp430_devices = find_430_macOS()
    elif current_os == "Linux":
        msp430_devices = find_430_Linux()

    shell(msp430_devices)
