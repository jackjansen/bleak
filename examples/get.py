"""
Get value for a single characteristic

"""

import sys
import platform
import asyncio
import logging
import re

from bleak import BleakScanner
from bleak.pythonic.client import BleakPythonicClient

device = sys.argv[1]
characteristic = sys.argv[2]


async def run(device, charachteristic):
    # If the device is specified by name we look it up
    if re.fullmatch("[0-9a-fA-F:-]*", device):
        dev = await BleakScanner.find_device_by_address(device)
    else:
        dev = await BleakScanner.find_device_by_filter(
            lambda d, ad: d.name and d.name.lower() == device
        )
    if not dev:
        print(f"Device {device} not found")
        return
    async with BleakPythonicClient(dev) as client:
        value = await client.read_gatt_char_typed(characteristic)
    print(value)


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.set_debug(True)
    loop.run_until_complete(run(device, characteristic))
