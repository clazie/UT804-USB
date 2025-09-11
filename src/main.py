from pywinusb import hid

cmds = [
    ['data?;', 'Read the current test data', 'ro', 'double'],
    ['disp?;', 'Read the current test data and status information, that is reading display on the screen.', 'ro', 'double']
]


print('--------------------------------')
print('Listing all HID devices')
print('--------------------------------')

all_hids = hid.find_all_hid_devices()

for d in all_hids:
  print(d)

print('--------------------------------')
print('Searching for a UT804 device')
print('--------------------------------')

filter = hid.HidDeviceFilter(vendor_id=0x1a86, product_id=0xe008)
devices = filter.get_devices()

if(len(devices) == 0):
    print("No device found")
    exit(1)

print(f'found {len(devices)} device(s):')

for d in devices:
  print(d)

print('--------------------------------')
print('Using the first device')
print('--------------------------------')

device = devices[0]
print(device)


def readData(data):
    print(data)
    return None


device.set_raw_data_handler(readData)
device.open()
input("Press Enter to continue...")
device.close()
