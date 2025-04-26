import asyncio
from bleak import BleakClient, BleakScanner

# UUIDs
SERVICE_UUID_1 = "12345678-1234-1234-1234-1234567890ab"
CHARACTERISTIC_UUID_1 = "abcdefab-1234-5678-1234-abcdefabcdef"

SERVICE_UUID_2 = "87654321-4321-4321-4321-0987654321ba"
CHARACTERISTIC_UUID_2 = "fedcbafe-4321-8765-4321-fedcbafedcba"

# ESP32 advertised names
DEVICE_NAME_1 = "ESP32_Sender"
DEVICE_NAME_2 = "ESP32_Receiver"

# Global buffer for collecting incoming data from ESP32 #1
data_buffer = bytearray()

# Clients (global so accessible inside callbacks)
client1 = None
client2 = None

async def handle_notify(sender, data):
    """Callback function when notification received from ESP32 #1."""
    global data_buffer

    print(f"Received from ESP32 #1: {list(data)}")

    # Add received data to buffer
    data_buffer.extend(data)

    # Process buffer in 10-byte chunks
    while len(data_buffer) >= 10:
        chunk = data_buffer[:10]
        data_buffer = data_buffer[10:]

        # Frame the chunk with 0xAA header
        framed_data = bytes([0xAA]) + chunk

        # Send framed data to ESP32 #2
        await client2.write_gatt_char(CHARACTERISTIC_UUID_2, framed_data)
        print(f"Sent to ESP32 #2 (with header): {list(framed_data)}")

async def main():
    global client1, client2

    print("Scanning for devices...")

    devices = await BleakScanner.discover()
    address1 = None
    address2 = None

    for d in devices:
        if d.name == DEVICE_NAME_1:
            address1 = d.address
        elif d.name == DEVICE_NAME_2:
            address2 = d.address

    if not address1 or not address2:
        print("Could not find both devices!")
        print(f"Found addresses so far: {[d.name for d in devices]}")
        return

    print(f"Found devices:")
    print(f"ESP32_Sender at {address1}")
    print(f"ESP32_Receiver at {address2}")

    client1 = BleakClient(address1)
    client2 = BleakClient(address2)

    # Connect to both devices
    async with client1, client2:
        await client1.connect()
        await client2.connect()

        print("Connected to both ESP32 #1 and ESP32 #2!")

        # Start listening to ESP32 #1 notifications
        await client1.start_notify(CHARACTERISTIC_UUID_1, handle_notify)

        print("Listening for notifications from ESP32 #1...")

        # Keep running indefinitely
        while True:
            await asyncio.sleep(1)

if __name__ == "__main__":
    asyncio.run(main())
