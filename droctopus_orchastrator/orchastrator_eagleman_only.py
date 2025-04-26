import asyncio
from bleak import BleakClient, BleakScanner

# UUIDs (same as before)
SERVICE_UUID_2 = "87654321-4321-4321-4321-0987654321ba"
CHARACTERISTIC_UUID_2 = "fedcbafe-4321-8765-4321-fedcbafedcba"

# ESP32 advertised name
DEVICE_NAME_2 = "ESP32_Receiver"

async def send_user_commands():
    print("Scanning for ESP32_Receiver...")

    devices = await BleakScanner.discover()
    address2 = None

    for d in devices:
        if d.name == DEVICE_NAME_2:
            address2 = d.address

    if not address2:
        print("Could not find ESP32_Receiver!")
        return

    print(f"Found ESP32_Receiver at {address2}")

    client2 = BleakClient(address2)

    async with client2:
        await client2.connect()
        print("Connected to ESP32_Receiver!")

        while True:
            try:
                # Get user input
                user_input = input("Enter 10 integers (0-255) separated by spaces: ")
                numbers = user_input.strip().split()

                # Validate
                if len(numbers) != 10:
                    print("Error: You must enter exactly 10 integers.")
                    continue

                try:
                    byte_values = [int(x) for x in numbers]
                except ValueError:
                    print("Error: Please enter only valid integers.")
                    continue

                if any(not (0 <= b <= 255) for b in byte_values):
                    print("Error: Integers must be between 0 and 255.")
                    continue

                # Frame with 0xAA header
                framed_data = bytes([0xAA] + byte_values)

                # Send to ESP32_Receiver
                await client2.write_gatt_char(CHARACTERISTIC_UUID_2, framed_data)
                print(f"Sent: {[hex(b) for b in framed_data]}")

            except KeyboardInterrupt:
                print("\nExiting...")
                break

if __name__ == "__main__":
    asyncio.run(send_user_commands())
