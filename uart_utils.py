import glob
import logging
import platform
import subprocess
import os

logger = logging.getLogger('uart_utils')

# USB IDs from Windows driver INF files under C:\ti\ccs_base\emulation\windows\xds110_drivers
# Those drivers are installed by Emupack from https://software-dl.ti.com/ccs/esd/documents/xdsdebugprobes/emu_xds_software_package_download.html
# Note: after installing Windows drivers, devmgmt.msc will show devices with the name specified in INF files
XDS110_DEBUG_PORTS = [
    # xds110_ports.inf
    r'USB\VID_0451&PID_BEF3&MI_03',
    r'USB\VID_0451&PID_BEF4&MI_03',
    r'USB\VID_1CBE&PID_029E&MI_03',
    r'USB\VID_1CBE&PID_02A5&MI_04',
    # xds110_cmsis20.inf
    r'USB\VID_1CBE&PID_02A5&MI_00',
    # xds110_debug.inf
    r'USB\VID_0451&PID_BEF3&MI_02',
    r'USB\VID_0451&PID_BEF4&MI_02',
    r'USB\VID_1CBE&PID_029E&MI_02',
    r'USB\VID_1CBE&PID_029F&MI_00',
    r'USB\VID_1CBE&PID_029F&MI_01',
]

# USB IDs from Windows driver INF, extracted from CP210X_USB_Driver.zip
# BK9171B uses CP2102. It's unlikely that we need to run minicom with it.
# See: https://www.bkprecision.com/products/power-supplies/9171B-dual-range-dc-power-supply-10v-10a-20v-5a.html
CP210X_PORTS = [
    # slabvcp.inf
    r'USB\VID_10C4&PID_EA60&MI_00',
    r'USB\VID_10C4&PID_EA63&MI_00',
    r'USB\VID_10C4&PID_EA70&MI_00',
    r'USB\VID_10C4&PID_EA70&MI_01',
    r'USB\VID_10C4&PID_EA71&MI_00',
    r'USB\VID_10C4&PID_EA71&MI_01',
    r'USB\VID_10C4&PID_EA71&MI_02',
    r'USB\VID_10C4&PID_EA71&MI_03',
    r'USB\VID_10C4&PID_EA7A&MI_00',
    r'USB\VID_10C4&PID_EA7A&MI_01',
    r'USB\VID_10C4&PID_EA7B&MI_00',
    r'USB\VID_10C4&PID_EA7B&MI_01',
    r'USB\VID_10C4&PID_EA7B&MI_02',
    r'USB\VID_10C4&PID_EA7B&MI_03',
]

def load_libmsp430():
    from ctypes import CDLL

    LIBRARY_NAME = 'libmsp430.so'
    library_candidates = [LIBRARY_NAME]
    path_candidates = [
        f'~/ti/*/ccs/ccs_base/DebugServer/drivers/{LIBRARY_NAME}'
    ]

    for path_candidate in path_candidates:
        library_candidates.extend(glob.glob(os.path.expanduser(path_candidate)))
    for library_candidate in library_candidates:
        try:
            return CDLL(library_candidate)
        except OSError:
            pass

def find_msp430_usb_interfaces():
    from ctypes import POINTER, c_char_p, c_int32

    libmsp430 = load_libmsp430()
    if not libmsp430:
        logger.info('libmsp430.so is not found, skipping detection of MSP430 debugging interfaces')
        return []

    # Adopted from the example in https://www.ti.com/lit/ug/slau656b/slau656b.pdf
    STATUS_OK = 0
    MSP430_GetNumberOfUsbIfs = libmsp430.MSP430_GetNumberOfUsbIfs
    MSP430_GetNumberOfUsbIfs.argtypes = (
        POINTER(c_int32),   # int32_t* Number
    )
    MSP430_GetNumberOfUsbIfs.restype = c_int32
    MSP430_GetNameOfUsbIf = libmsp430.MSP430_GetNameOfUsbIf
    MSP430_GetNameOfUsbIf.argtypes = (
        c_int32,            # int32_t Idx
        POINTER(c_char_p),  # char** Name
        POINTER(c_int32),   # int32_t* Status
    )
    MSP430_Error_Number = libmsp430.MSP430_Error_Number
    MSP430_Error_Number.argtypes = ()
    MSP430_Error_Number.restype = c_int32

    interface_names = []

    number = c_int32()
    if MSP430_GetNumberOfUsbIfs(number) != STATUS_OK:
        logger.error('Could not determine number of USB interfaces. Error = ', MSP430_Error_Number().value)
        return

    for idx in range(number.value):
        name = c_char_p()
        status = c_int32()
        if MSP430_GetNameOfUsbIf(idx, name, status) != STATUS_OK:
            logger.error('Could not obtain port name of USB interface. Error = ', MSP430_Error_Number().value)
            continue
        interface_names.append(name.value.decode('ascii'))

    logger.debug('Found %s USB debugging interfaces: %s', number.value, ', '.join(interface_names))

    return interface_names

def filter_xds110_debug_ports(interfaces):
    ret = []
    for interface in interfaces:
        udev_info = subprocess.check_output(['udevadm', 'info', f'--name={interface}']).decode('utf-8').strip()
        vendor_id = model_id = ifnum = None
        for line in udev_info.split('\n'):
            line = line.split(':')[1].strip()
            if '=' not in line:
                continue
            key, value = line.split('=')
            if key == 'ID_VENDOR_ID':
                vendor_id = value.upper()
            elif key == 'ID_MODEL_ID':
                model_id = value.upper()
            elif key == 'ID_USB_INTERFACE_NUM':
                ifnum = value
        full_id = f'USB\\VID_{vendor_id}&PID_{model_id}&MI_{ifnum}'
        logger.debug('Full ID: ' + full_id)
        if full_id in XDS110_DEBUG_PORTS:
            logger.info(f'{interface} is detected as an XDS110 debug port ({full_id}), skipping...')
            continue
        if full_id in CP210X_PORTS:
            logger.info(f'{interface} is detected as a CP210X port, skipping...')
            continue
        ret.append(interface)
    return ret

def find_uart_macOS():
    """
    Find UART device path
        args: None
        return: [path_to_dev]
    """
    DEVICE_PATH = "/dev"
    devices = os.listdir(DEVICE_PATH)
    usb_devices = [dev for dev in devices if dev.startswith("cu.usbmodem")]
    usb_devices.sort()
    uart_terminals = [os.path.join(DEVICE_PATH, dev)
                      for dev in usb_devices if dev.endswith("03")]

    return uart_terminals

def find_uart_Linux():
    msp430_usb_interfaces = find_msp430_usb_interfaces()
    ret = []
    for serial_interface in glob.glob("/dev/serial/by-id/*"):
        serial_interface_basename = os.path.basename(os.readlink(serial_interface))
        if serial_interface_basename in msp430_usb_interfaces:
            logger.info('%s (%s) is detected as a debugging interface, skipping...',
                        serial_interface, serial_interface_basename)
            continue
        ret.append(serial_interface)
    return sorted(filter_xds110_debug_ports(ret))

def find_uart():
    current_os = platform.system()
    if current_os == "Darwin": # macOS
        return find_uart_macOS()
    elif current_os == "Linux":
        return find_uart_Linux()
