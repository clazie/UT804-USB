import pywinusb.hid as hid
import time
# import struct

# Logging constants
DEBUG = True
INFO = True

# Color constants
OKGRAY = '\033[0;90m'
OKCYAN = '\033[96m'
OKGREEN = '\033[92m'
WARNING = '\033[93m'
FAIL = '\033[91m'
ENDC = '\033[0m'

# Decodings
CUPPLING = [
    'DC',
    'AC',
    'AC+DC'
]

MEASUREMENT = [
    'V=',
    'V~',
    'mV=',
    'Ohm',
    'F',
    '°C',
    'µA',
    'mA',
    'A',
    'Pieps',
    'Diode',
    'Hz (oder Tastverhältnis)',
    '°F',
    '-',
    '% (4-20-mA-Tester)'
]

INFO = [
    '      ',  # 48 '0'
    'Auto +',  # 49 '1'
    'Man  +',  # 50 '2'
    '      ',  # 51 '3'
    '     -',  # 52 '4'
    'Auto -',  # 53 '5'
    'Man  -',  # 54 '6'
    '      ',  # 55 '7'
    '      ',  # 56 '8'
    '      '   # 57 '9'
]


# Global vars
receivebytes: bytes = []
lastrecbytes: bytes = []


def Log(msg: str):
  if (DEBUG or INFO):
    print(f'{OKCYAN}{msg}{ENDC}')


def Info(msg: str):
  if (INFO):
    print(f'{OKCYAN}{msg}{ENDC}')


def Debug(msg: str):
  if (DEBUG):
    print(f'{OKGRAY}{msg}{ENDC}')


def Warn(msg: str):
  print(f'{WARNING}{msg}{ENDC}')


def Error(msg: str):
  print(f'{FAIL}{msg}{ENDC}')


def listAllHidDevices():
    print('--------------------------------')
    print('Listing all HID devices')
    print('--------------------------------')

    all_hids = hid.find_all_hid_devices()
    for d in all_hids:
        print(d)


def getFirstHidDevicesByVendorProduct(vendor_id, product_id):
    print('--------------------------------')
    print(f'Listing all HID devices with vendor_id=0x{vendor_id:04x}, product_id=0x{product_id:04x}')
    print('--------------------------------')

    filter = hid.HidDeviceFilter(vendor_id=vendor_id, product_id=product_id)
    devices: list = filter.get_devices()

    if (len(devices) == 0):
        print("No device found")
        return None

    print(f'found {len(devices)} device(s):')

    for d in devices:
        print(d)
        return devices[0]
    return None


def getOutReport(device):
    out_reports = device.find_output_reports()
    print(f'Found {len(out_reports)} output report(s)')

    for i in range(len(out_reports)):
        print(f"Output report {i}: {out_reports[i]}")

    if (len(out_reports) == 1):
        print("Using the first output report")
        return out_reports[0]
    return None


def getInReport(device):
    in_reports = device.find_output_reports()
    print(f'Found {len(in_reports)} output report(s)')

    for i in range(len(in_reports)):
        print(f"Output report {i}: {in_reports[i]}")

    if (len(in_reports) == 1):
        print("Using the first output report")
        return in_reports[0]
    return None


def getFeatureReport(device):
    feature_reports = device.find_feature_reports()
    print(f'Found {len(feature_reports)} feature report(s)')

    for i in range(len(feature_reports)):
        print(f"Feature report {i}: {feature_reports[i]}")

    if (len(feature_reports) == 1):
        print("Using the first feature report")
        return feature_reports[0]
    return None


def readDataHandler(data):
    global receivebytes
    global lastrecbytes

    datacount = data[1] & 0x07
    # print(datacount)
    if (datacount > 0):  # data not empty
      Log(f"Raw data: {data}")
      for i in range(datacount):
        receivebytes.append(data[i + 2] & 0x7F)
        print(f"Data[{i}] = {data[i + 2]} ({chr(data[i + 2])})")

    length = len(receivebytes)
    # print(f'len(receivebytes)={length}')

    if ((length > 0) and (receivebytes[length - 1] == 10)):  # end of string (\n)
      print(f'{receivebytes} done')
      lastrecbytes = bytes(receivebytes)
      receivebytes = []

    return None


def calcValue(valuestr: str, factor: int, info: int, corr: int = 0) -> float:
  try:
    # if (len(s) < 8):
    #   raise ValueError('Not a valid value')

    # factor = int(s[5:6].decode('ascii'))
    # valstr: str = s[0:5].decode('ascii')

    if (valuestr == '::0<:'):
      raise ValueError('Overload')

    valint = int(valuestr)
    value = float(valint / 100000 * (10 ** (factor + corr)))
    value = round(value, 5)

    if ((info[5] == '-')):  # Negative sign
      value = -value

  except ValueError as e:
    Warn(f'Value error: {e}')
    value = 99999999.9  # Error value
  except Exception as e:
    Error(f'General error: {e}')
    value = 99999999.9  # Error value
  return value


def decodeStr(b: bytes):
    Debug(f'Data: {b}')
    Debug(f'{b[0:5].decode()} {chr(b[6])} {chr(b[7])} {chr(b[8])}')

    # 0-4 Wertestring
    valuestr: str = f'{b[0:5].decode()}'
    Debug(f'ValueStr: {valuestr}')

    # 5 Bereich
    factor: int = int(chr(b[5]))
    Debug(f'Factor: {factor}')

    # 6 Schalter
    measurement: str = MEASUREMENT[int(b[6] - 48)]
    Debug(f'MEASUREMENT: {measurement}')

    # 7 Kopplung
    cuppling: str = CUPPLING[b[7] - 48]
    Debug(f'Cuppling: {cuppling}')

    # 8 Info
    info: str = INFO[int(b[8] - 48)]
    Debug(f'Info: {info}')

    # Wert mit Faktor
    value: float = float(calcValue(valuestr, factor, info))
    Debug(f'Value: {value}')

    Info(f'{cuppling}{measurement} {value} Faktor: {factor}, Info: {info}')


def writeBuffer(report, buffer):
    print(buffer)
    report.set_raw_data(buffer)
    ret = report.send()
    time.sleep(0.1)
    return int(ret)


def writeData(report, data):
    buffer = [0x00] * 9  # 9 bytes buffer
    buffer[0] = 0  # report ID
    buffer[1] = 9  # Data Length
    buffer[1:7] = data[0:6]  # Data
    buffer[7] = 0  # checksum
    buffer[8] = 0
    return int(writeBuffer(report, buffer))


listAllHidDevices()
device: hid.HidDevice = getFirstHidDevicesByVendorProduct(0x1a86, 0xe008)
if (device is None):
    print("No device to open")
    exit(1)

device.open()
device.set_raw_data_handler(readDataHandler)
out_report = getOutReport(device)
in_report = getInReport(device)

print(writeData(in_report, b'data?;'))

# Turn on Serial communication
feature_report = getFeatureReport(device)
# baudrate 60 09 -> 0x0960 = 2400
# baudrate C0 12 -> 0x12C0 = 4800
# baudrate 80 25 -> 0x2580 = 9600
#                                  0     baud     2     3     4     5
print(writeBuffer(feature_report, [0x00, 0x4b, 0x00, 0x00, 0x03, 0x00]))
# print(writeBuffer(feature_report, [0x00, 0x60, 0x09, 0x00, 0x00, 0x03]))


try:
    print("Device is open")
    while (device.is_plugged()):
        # print(writeData(out_report, b'disp?;'))
        # time.sleep(1)
        if(len(lastrecbytes) > 0):
          if (len(lastrecbytes) == 11):
            decodeStr(lastrecbytes)
          else:
            print(f'Error: Stringlength is wrong: {len(lastrecbytes)})')
          lastrecbytes = []

        # print(writeData(out_report, b'data?;'))
        # time.sleep(1)
        # print(f'Received data string: {lastrecstr}')
        # lastrecstr = ''

        # print(writeData(in_report, b'data?;'))
        # time.sleep(1)
        # print(writeData(feature_report, b'data?;'))
        # time.sleep(1)
        # print(writeData(out_report, b'disp?;'))
        # time.sleep(1)
        # print(writeData(in_report, b'disp?;'))
        # time.sleep(1)
        # print(writeData(feature_report, b'disp?;'))
        # time.sleep(1)


except KeyboardInterrupt as e:
    print("KeyboardInterrupt")
    print(e)
finally:
    print("Finally")
    device.close()
    print("Device is closed")

exit(0)
