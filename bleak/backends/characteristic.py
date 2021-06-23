# -*- coding: utf-8 -*-
"""
Interface class for the Bleak representation of a GATT Characteristic

Created on 2019-03-19 by hbldh <henrik.blidh@nedomkull.com>

"""
import abc
import enum
from uuid import UUID
from typing import List, Union, Any
import struct

from bleak.backends.descriptor import BleakGATTDescriptor
from bleak.uuids import uuidstr_to_str


class GattCharacteristicsFlags(enum.Enum):
    broadcast = 0x0001
    read = 0x0002
    write_without_response = 0x0004
    write = 0x0008
    notify = 0x0010
    indicate = 0x0020
    authenticated_signed_writes = 0x0040
    extended_properties = 0x0080
    reliable_write = 0x0100
    writable_auxiliaries = 0x0200

def str2bytes(s : str) -> bytes:
    return s.encode('utf8')

def bytes2str(b : bytes) -> str:
    return b.decode('utf8')

Table_2904_bytes_format = {
    1 : (bool, bool, 1, '?'),   # Boolean
    2 : (int, int, 1, 'B'),   # unsigned 2-bit int
    3 : (int, int, 1, 'B'),   # unsigned 4-bit int
    4 : (int, int, 1, 'B'),   # unsigned 8-bit int
    5 : (int, int, 2, 'H'),   # unsigned 12-bit int
    6 : (int, int, 2, 'H'),   # unsigned 16-bit int
#    7 : (int, int, 3, ''),   # unsigned 24-bit int
    8 : (int, int, 4, 'I'),   # unsigned 32-bit int
#    9 : (int, int, 6, ''),   # unsigned 48-bit int
    10 : (int, int, 8, 'Q'),   # unsigned 64-bit int
#    11 : (int, int, 16, ''),   # unsigned 128-bit int
    12 : (int, int, 1, 'b'),   # 8-bit int
    13 : (int, int, 2, 'h'),   # 12-bit int
    14 : (int, int, 2, 'h'),   # 16-bit int
#    15 : (int, int, 3, ''),   # 24-bit int
    16 : (int, int, 4, 'i'),   # 32-bit int
#    17 : (int, int, 6, ''),   # 48-bit int
    18 : (int, int, 8, 'Q'),   # 64-bit int
#    19 : (int, int, 16, ''),   # 128-bit int
    20 : (float, float, 4, 'f'),   # 32-bit float
    21 : (float, float, 8, 'd'),   # 64-bit double
    25 : (str2bytes, bytes2str, None, None), # UTF8 string
    27 : (bytes, bytes, None, None), # Opaque structure    
}

Table_uuid_to_marshaller = {}

class BleakGATTMarshaller(abc.ABC):
    @classmethod
    def get_marshaller(klass, descr_2904=None, uuid=None) -> Any:
        if uuid:
            if uuid in Table_uuid_to_marshaller:
                return Table_uuid_to_marshaller[uuid]()
        if descr_2904:
            format, exponent, unit, namespace, description = struct.unpack("BbHBH", descr_2904)
            if format in Table_2904_bytes_format:
                return BleakGATTPackMarshaller(format, exponent, unit)
        return BleakGATTMarshaller()

    @staticmethod
    def marshall(data : Any) -> bytes:
        return bytes(data)

    @staticmethod
    def unmarshall(data_bytes : bytes) -> Any:
        return data_bytes

class BleakGATTPackMarshaller(BleakGATTMarshaller):

    def __init__(self, format, exponent, unit):
        self.frompython, self.topython, self.length, self.format = format
        self.exponent = exponent
        self.unit = unit

    def marshall(self, data : Any) -> bytes:
        if not self.length:
            return self.frompython(data)
        # xxxjack exponent
        # xxxjack unit?
        data = self.frompython(data)
        data_bytes = struct.pack(self.format, data)
        assert len(data_bytes) == self.length
        return data_bytes

    def unmarshall(self, data_bytes : bytes) -> Any:
        if not self.length:
            return self.topython(data_bytes)
        assert len(data_bytes) == self.length
        print(f"xxxjack format={self.format}, data_bytes={data_bytes}")
        data = struct.unpack(self.format, data_bytes)
        # xxxjack exponent
        # xxxjack unit?
        return data

class BleakGATTCharacteristic(abc.ABC):
    """Interface for the Bleak representation of a GATT Characteristic"""

    def __init__(self, obj: Any):
        self.obj = obj

    def __str__(self):
        return f"{self.uuid} (Handle: {self.handle}): {self.description}"

    @property
    @abc.abstractmethod
    def service_uuid(self) -> str:
        """The UUID of the Service containing this characteristic"""
        raise NotImplementedError()

    @property
    @abc.abstractmethod
    def service_handle(self) -> int:
        """The integer handle of the Service containing this characteristic"""
        raise NotImplementedError()

    @property
    @abc.abstractmethod
    def handle(self) -> int:
        """The handle for this characteristic"""
        raise NotImplementedError()

    @property
    @abc.abstractmethod
    def uuid(self) -> str:
        """The UUID for this characteristic"""
        raise NotImplementedError()

    @property
    def description(self) -> str:
        """Description for this characteristic"""
        return uuidstr_to_str(self.uuid)

    @property
    @abc.abstractmethod
    def properties(self) -> List[str]:
        """Properties of this characteristic"""
        raise NotImplementedError()

    @property
    @abc.abstractmethod
    def descriptors(self) -> List:
        """List of descriptors for this service"""
        raise NotImplementedError()

    @abc.abstractmethod
    def get_descriptor(
        self, specifier: Union[int, str, UUID]
    ) -> Union[BleakGATTDescriptor, None]:
        """Get a descriptor by handle (int) or UUID (str or uuid.UUID)"""
        raise NotImplementedError()

    def get_marshaller(self) -> BleakGATTMarshaller:
        descr_2904 = self.get_descriptor("00002904-0000-1000-8000-00805f9b34fb")
        return BleakGATTMarshaller.get_marshaller(descr_2904=descr_2904, uuid=self.uuid)

    @abc.abstractmethod
    def add_descriptor(self, descriptor: BleakGATTDescriptor):
        """Add a :py:class:`~BleakGATTDescriptor` to the characteristic.

        Should not be used by end user, but rather by `bleak` itself.
        """
        raise NotImplementedError()
