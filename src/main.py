import pywinusb.hid as hid
import time
# import struct

# Logging constants
DEBUG = False
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
    '--',
    'AC+DC'
]

MEASUREMENT = [
    '  ',
    'V=',
    'V~',
    'mV=',
    'Ohm',
    'µF',
    '°C',
    'µA',
    'mA',
    'A',
    'Beep',
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


# Logging functions
def Log(msg: str):
  if (DEBUG or INFO):
    print(f'{OKGREEN}{msg}{ENDC}')


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


# USB-Hid functions
def listAllHidDevices():
    Debug('--------------------------------')
    Debug('Listing all HID devices')
    Debug('--------------------------------')

    all_hids = hid.find_all_hid_devices()
    for d in all_hids:
        Debug(d)


def writeBuffer(report, buffer):
    Debug(buffer)
    report.set_raw_data(buffer)
    ret = report.send()
    time.sleep(0.1)
    return int(ret)

# def readBuffer(report, buffer):
#     Debug(buffer)
#     report.set_raw_data(buffer)
#     ret = report.send()
#     time.sleep(0.1)
#     return int(ret)


def writeData(report, data):
    buffer = [0x00] * 9  # 9 bytes buffer
    buffer[0] = 0  # report ID
    buffer[1] = 9  # Data Length
    buffer[1:7] = data[0:6]  # Data
    buffer[7] = 0  # checksum
    buffer[8] = 0
    return int(writeBuffer(report, buffer))


def getFirstHidDevicesByVendorProduct(vendor_id, product_id):
    Info('--------------------------------')
    Info(f'Listing all HID devices with vendor_id=0x{vendor_id:04x}, product_id=0x{product_id:04x}')
    Info('--------------------------------')

    filter = hid.HidDeviceFilter(vendor_id=vendor_id, product_id=product_id)
    devices: list = filter.get_devices()

    if (len(devices) == 0):
        Error("No device found")
        return None

    Info(f'found {len(devices)} device(s):')

    for d in devices:
        Info(d)
        return devices[0]
    return None


def getOutReport(device):
    out_reports = device.find_output_reports()
    Debug(f'Found {len(out_reports)} output report(s)')

    for i in range(len(out_reports)):
        Debug(f"Output report {i}: {out_reports[i]}")

    if (len(out_reports) == 1):
        Debug("Using the first output report")
        return out_reports[0]
    return None


def getInReport(device):
    in_reports = device.find_input_reports()
    Debug(f'Found {len(in_reports)} input report(s)')

    for i in range(len(in_reports)):
       Debug(f"Input report {i}: {in_reports[i]}")

    if (len(in_reports) == 1):
        Debug("Using the first input report")
        return in_reports[0]
    return None


def getFeatureReport(device):
    feature_reports = device.find_feature_reports()
    Debug(f'Found {len(feature_reports)} feature report(s)')

    for i in range(len(feature_reports)):
        Debug(f"Feature report {i}: {feature_reports[i]}")

    if (len(feature_reports) == 1):
        Debug("Using the first feature report")
        return feature_reports[0]
    return None


def readDataHandler(data):
    global receivebytes
    global lastrecbytes

    datacount = data[1] & 0x07
    Debug(f'Datacount: {datacount}')
    if (datacount > 0):  # data not empty
      Debug(f"Raw data: {data}")
      for i in range(datacount):
        receivebytes.append(data[i + 2] & 0x7F)
        Debug(f"Data[{i}] = {data[i + 2]} ({chr(data[i + 2])})")

    length = len(receivebytes)
    Debug(f'len(receivebytes)={length}')

    if ((length > 0) and (receivebytes[length - 1] == 10)):  # end of string (\n)
      Debug(f'{receivebytes} done')
      lastrecbytes = bytes(receivebytes)
      receivebytes = []

    return None


# Value functions
def calcValue(valuestr: str, factor: int, info: int, measurementidx: int) -> float:
  try:
    # if (len(s) < 8):
    #   raise ValueError('Not a valid value')

    # factor = int(s[5:6].decode('ascii'))
    # valstr: str = s[0:5].decode('ascii')

    # correction factor
    corr = 0
    match measurementidx:
       case 0:
          corr = 0
       case 1:  # V=
          corr = 0
       case 2:  # V~
          corr = 0
       case 3:  # mV=
          corr = 3
       case 4:  # Ohm
          corr = 2
       case 5:  # Cap
          corr = -2
       case 6:  # °C
          corr = 4
       case 7:  # µA
          corr = 3
       case 8:  # mA
          corr = 2
       case 9:  # A
          corr = 1
       case 10:  # Beep
          corr = 3
       case 11:  # Diode
          corr = 1
       case 12:  # Hz (oder Tastverhältnis)
          if (info[5] == '-'):
             corr = 3
          else:
             corr = 2
       case 13:  # °F
          corr = 4
       case 14:  # -
          corr = 0
       case 15:  # % (4-20-mA-Tester)
          corr = 3

    # overload detection
    if (valuestr == '::0<:'):
      raise ValueError('Overload')

    valint = int(valuestr)
    value = float(valint / 100000 * (10 ** (factor + corr)))
    value = round(value, 5)

    if ((measurementidx != 12) and (info[5] == '-')):  # Negative sign
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
    measurementindex = int(b[6] - 48)
    measurement: str = MEASUREMENT[measurementindex]
    Debug(f'MEASUREMENT: {measurement}')

    # 7 Kopplung
    cuppling: str = CUPPLING[b[7] - 48]
    Debug(f'Cuppling: {cuppling}')

    # 8 Info
    info: str = INFO[int(b[8] - 48)]
    Debug(f'Info: {info}')

    # Wert mit Faktor
    value: float = float(calcValue(valuestr, factor, info, measurementindex))
    Debug(f'Value: {value}')

    Log(f'{cuppling}{measurement} {value} Faktor: {factor}, Info: {info}')


# main program
listAllHidDevices()
device: hid.HidDevice = getFirstHidDevicesByVendorProduct(0x1a86, 0xe008)
if (device is None):
    Error("No device to open")
    exit(1)

device.open()
device.set_raw_data_handler(readDataHandler)
out_report = getOutReport(device)
# in_report = getInReport(device)

Debug(writeData(out_report, b'data?;'))

# Turn on Serial communication
feature_report = getFeatureReport(device)
# baudrate 60 09 -> 0x0960 = 2400
# baudrate C0 12 -> 0x12C0 = 4800
# baudrate 80 25 -> 0x2580 = 9600
# Not working????
Debug(writeBuffer(feature_report, [0x00, 0x4b, 0x00, 0x00, 0x03, 0x00]))

Warn('Press Ctrl+C to terminate program')
try:
    Log("Device is open")
    while (device.is_plugged()):
      if(len(lastrecbytes) > 0):
        if (len(lastrecbytes) == 11):
          decodeStr(lastrecbytes)
        else:
          Warn(f'Error: Stringlength is wrong: {len(lastrecbytes)})')
        lastrecbytes = []
except KeyboardInterrupt as e:
    Warn("KeyboardInterrupt")
    Warn(e)
finally:
    Log("Finally")
    device.close()
    Log("Device is closed")

exit(0)
