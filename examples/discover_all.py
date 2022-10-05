"""
Scan/Discovery
--------------

Example showing how to scan for BLE devices.

Updated on 2019-03-25 by hbldh <henrik.blidh@nedomkull.com>

"""

import asyncio

from bleak import BleakScanner, BLEDevice, AdvertisementData, BleakError
from bleak import uuids
from bleak.pythonic.client import BleakPythonicClient

DEVICES_SEEN_BEFORE = {}

async def detection_callback(device : BLEDevice, advData : AdvertisementData):
    if device.name and device.name != "Unknown":
        device_name = device.name
    else:
        device_name = device.address
    if device_name in DEVICES_SEEN_BEFORE:
        return
    print(f"{device_name}:")
    DEVICES_SEEN_BEFORE[device_name] = True
    async with BleakPythonicClient(device) as conn:
        services_seen_before = {}
        for s in conn.services:
            service_uuid = s.uuid
            service_name = uuids.uuidstr_to_str(service_uuid)
            if not service_name or service_name == "Unknown":
                if s.description and s.description != "Unknown":
                    service_name = s.description
                else:
                    service_name = service_uuid
            if service_name in services_seen_before:
                continue
            services_seen_before[service_name] = True
            print(f"\t{service_name}:")
            chars_seen_before = {}
            for c in s.characteristics:
                char_uuid = c.uuid
                char_name = uuids.uuidstr_to_str(char_uuid)
                if not char_name or char_name == "Unknown":
                    if c.description and c.description != "Unknown":
                        char_name = c.description
                    else:
                        char_name = char_uuid
                if char_name == chars_seen_before:
                    continue
                chars_seen_before[char_name] = True
                print(f"\t\t{char_name}:")
                try:
                    value = await conn.read_gatt_char_typed(c)
                    print(f"\t\t\t{value}")
                except BleakError as e:
                    print(f"\t\t\tError: {e}")

EXECUTE_ASYNC = False
async def main():
    if EXECUTE_ASYNC:
        scanner = BleakScanner(detection_callback=detection_callback)
        await scanner.start()
        await asyncio.sleep(10)
        await scanner.stop()
    else:
        devices = await BleakScanner.discover(10)
        for d in devices:
            await detection_callback(d, None)

if __name__ == "__main__":
    asyncio.run(main())
