from typing import Union, Any
import uuid
from bleak import BleakClient
from bleak.exc import BleakError
from bleak.backends.characteristic import BleakGATTCharacteristic
from bleak.pythonic.marshall import BleakGATTMarshaller


class BleakPythonicClient(BleakClient):
    __doc__ = BleakClient.__doc__ + """
    
    This is a subclass of BleakClient, currently with only two methods
    added. To be extended with accessors.
    """
    async def read_gatt_char_typed(
        self,
        char_specifier: Union[BleakGATTCharacteristic, int, str, uuid.UUID],
        **kwargs
    ) -> Any:
        """Perform read operation on the specified GATT characteristic.
        The data returned is unmarshalled into native Python form based on the type information in the char_specifier.

        Args:
            char_specifier (BleakGATTCharacteristic): The characteristic to read from.
        Returns:
            The read data.

        """
        marshaller = await self.get_marshaller(char_specifier)
        data_bytes = await self.read_gatt_char(char_specifier, **kwargs)
        data = marshaller.unmarshall(data_bytes)
        return data

    async def write_gatt_char_typed(
        self,
        char_specifier: Union[BleakGATTCharacteristic, int, str, uuid.UUID],
        data: Any,
        response: bool = False,
    ) -> None:
        """Perform a write operation on the specified GATT characteristic.
        The data to write is marshalled based on the type information in the characteristic.

        Args:
            char_specifier (BleakGATTCharacteristic): The characteristic to write.
            data: The data to write.
            response (bool): If write-with-response operation should be done. Defaults to `False`.

        """
        marshaller = await self.get_marshaller(char_specifier)
        data_bytes = marshaller.marshall(data)
        return await self.write_gatt_char(char_specifier, data_bytes, response)

    async def get_marshaller(
        self, char_specifier: Union[BleakGATTCharacteristic, int, str, uuid.UUID]
    ) -> BleakGATTMarshaller:
        if not isinstance(char_specifier, BleakGATTCharacteristic):
            coll = await self.get_services()
            char = coll.get_characteristic(char_specifier)
            if not char:
                raise BleakError(f"Unknown characteristic {char_specifier}")
            char_specifier = char
        assert isinstance(char_specifier, BleakGATTCharacteristic)
        descr_2904 = char_specifier.get_descriptor(
            "00002904-0000-1000-8000-00805f9b34fb"
        )
        return await BleakGATTMarshaller.get_marshaller(
            descr_2904=descr_2904, uuid=char_specifier.uuid, client=self
        )
