# -*- coding: utf-8 -*-
from __future__ import annotations
import abc
import enum
from uuid import UUID
from typing import List, Union, Any
import struct
import warnings
from bleak import BleakClient


def str2bytes(s: str | bytes) -> bytes:
    # str2bytes also accepts bytes, because things like json-encode return bytes.
    if type(s) == bytes:
        return s
    return s.encode("utf8")


def bytes2str(b: bytes) -> str:
    return b.decode("utf8")


Table_2904_bytes_format = {
    1: (bool, bool, 1, "<?"),  # Boolean
    2: (int, int, 1, "<B"),  # unsigned 2-bit int
    3: (int, int, 1, "<B"),  # unsigned 4-bit int
    4: (int, int, 1, "<B"),  # unsigned 8-bit int
    5: (int, int, 2, "<H"),  # unsigned 12-bit int
    6: (int, int, 2, "<H"),  # unsigned 16-bit int
    #    7 : (int, int, 3, ''),   # unsigned 24-bit int
    8: (int, int, 4, "<I"),  # unsigned 32-bit int
    #    9 : (int, int, 6, ''),   # unsigned 48-bit int
    10: (int, int, 8, "<Q"),  # unsigned 64-bit int
    #    11 : (int, int, 16, ''),   # unsigned 128-bit int
    12: (int, int, 1, "<b"),  # 8-bit int
    13: (int, int, 2, "<h"),  # 12-bit int
    14: (int, int, 2, "<h"),  # 16-bit int
    #    15 : (int, int, 3, ''),   # 24-bit int
    16: (int, int, 4, "<i"),  # 32-bit int
    #    17 : (int, int, 6, ''),   # 48-bit int
    18: (int, int, 8, "<Q"),  # 64-bit int
    #    19 : (int, int, 16, ''),   # 128-bit int
    20: (float, float, 4, "<f"),  # 32-bit float
    21: (float, float, 8, "<d"),  # 64-bit double
    25: (str2bytes, bytes2str, None, None),  # UTF8 string
    27: (bytes, bytes, None, None),  # Opaque structure
}

# This table can be filled (eventually) with external marshaller sources.
# It could also be used for caching, if we think that is safe.
Table_uuid_to_marshaller = {}


class BleakGATTMarshaller(abc.ABC):
    """Marshall and unmarshall a GATT characteristic, converting between Python values and raw byte values."""

    @classmethod
    async def get_marshaller(
        klass, client: BleakClient, uuid: str, descr_2904=None
    ) -> Any:
        """Obtain a marshaller object."""
        if uuid:
            if uuid in Table_uuid_to_marshaller:
                return Table_uuid_to_marshaller[uuid]()
        if descr_2904:
            descr_2904_data = await client.read_gatt_descriptor(descr_2904.handle)
            format, exponent, unit, namespace, description = struct.unpack(
                "<BbHBH", descr_2904_data
            )
            if format in Table_2904_bytes_format:
                m = BleakGATTPackMarshaller(
                    Table_2904_bytes_format[format], exponent, unit
                )
                # We could add the marshaller to the table here, if we have a uuid
                return m
        warnings.warn(
            f"BleakGATTMarshaller: no marshaller found for client {client.address} characteristic {uuid}"
        )
        return BleakGATTMarshaller()

    @staticmethod
    def marshall(data: Any) -> bytes:
        """Convert data from Python format to raw bytes, for writing a characteristic."""
        return bytes(data)

    @staticmethod
    def unmarshall(data_bytes: bytes) -> Any:
        """Convert data from raw bytes to Python, for reading a characteristic."""
        return data_bytes


class BleakGATTPackMarshaller(BleakGATTMarshaller):
    def __init__(self, format, exponent, unit):
        self.frompython, self.topython, self.length, self.format = format
        self.exponent = exponent
        if self.exponent != 0:
            print(
                f"BleakGATTPackMarshaller: Warning: exponent not yet implemented",
                file=sys.stderr,
            )
        self.unit = unit
        # There does not seem to be anything useful to do with unit.

    def marshall(self, data: Any) -> bytes:
        if not self.length:
            return self.frompython(data)
        if self.exponent > 0:
            data = data / (10 ** self.exponent)
        elif self.exponent < 0:
            data = data * (10 ** -self.exponent)
        data = self.frompython(data)
        data_bytes = struct.pack(self.format, data)
        assert len(data_bytes) == self.length, f"Expected {self.length} bytes, got {len(data_bytes)}"
        return data_bytes

    def unmarshall(self, data_bytes: bytes) -> Any:
        if not self.length:
            return self.topython(data_bytes)
        assert len(data_bytes) == self.length, f"Expected {self.length} bytes, got {len(data_bytes)}"
        (data,) = struct.unpack(self.format, data_bytes)
        data = self.topython(data)
        if self.exponent != 0:
            data = data * (10.0 ** self.exponent)
        return data
