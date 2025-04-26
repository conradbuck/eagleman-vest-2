import reflex as rx
from reflex.components.chakra import circle, vstack, hstack, container, center, text, heading, button
import asyncio
from bleak import BleakClient, BleakScanner
import threading

# Global state to store motor values
class State(rx.State):
    # Initialize with default values
    motor_values: list[int] = [0] * 10
    connection_status: str = "Disconnected"
    
    def update_motors(self, values: list[int]):
        """Update motor values in the UI."""
        if len(values) == 10:
            self.motor_values = values


# UUIDs for BLE connection
SERVICE_UUID_2 = "87654321-4321-4321-4321-0987654321ba"
CHARACTERISTIC_UUID_2 = "fedcbafe-4321-8765-4321-fedcbafedcba"
DEVICE_NAME_2 = "ESP32_Receiver"

# Function to run the BLE client in a separate thread
def run_ble_client():
    asyncio.run(ble_client_loop())

async def ble_client_loop():
    """Main BLE client loop."""
    print("Scanning for ESP32_Receiver...")
    
    # Set global state to scanning
    State.connection_status = "Scanning..."
    yield
    
    devices = await BleakScanner.discover()
    address2 = None
    
    for d in devices:
        if d.name == DEVICE_NAME_2:
            address2 = d.address
    
    if not address2:
        print("Could not find ESP32_Receiver!")
        State.connection_status = "Device not found"
        yield
        return
    
    print(f"Found ESP32_Receiver at {address2}")
    State.connection_status = f"Found device at {address2}"
    yield
    
    client2 = BleakClient(address2)
    
    try:
        async with client2:
            await client2.connect()
            print("Connected to ESP32_Receiver!")
            State.connection_status = "Connected"
            yield
            
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
                    
                    # Update the UI state with the new values
                    State.update_motors(State, byte_values)
                    
                except KeyboardInterrupt:
                    print("\nExiting...")
                    break
                
    except Exception as e:
        print(f"Connection error: {e}")
        State.connection_status = f"Error: {str(e)}"
        yield


# Motor visualization component
def motor_circle(index: int, value: int) -> rx.Component:
    """Create an animated circle for each motor."""
    # Scale the value (0-255) to a reasonable size (20-80px)
    size = 20 + (value / 255) * 60
    
    # Define vibration animation using CSS
    vibration_style = {
        "@keyframes vibrate": {
            "0%": {"transform": "translate(0, 0)"},
            "25%": {"transform": "translate(-1px, 1px)"},
            "50%": {"transform": "translate(1px, -1px)"},
            "75%": {"transform": "translate(-1px, -1px)"},
            "100%": {"transform": "translate(0, 0)"}
        }
    }
    
    # More intense vibration for higher values
    animation_intensity = rx.cond(value > 20, "vibrate 0.1s infinite", "none")
    
    return center(
        vstack(
            circle(
                width=f"{size}px",
                height=f"{size}px",
                bg="blue.400",
                style=vibration_style,
                animation=animation_intensity,
                opacity=min(1.0, value / 150),  # Higher values are more opaque
            ),
            text(f"Motor {index+1}: {value}"),
        ),
        padding="1em",
    )


# Main page
def index() -> rx.Component:
    """The main view."""
    return container(
        vstack(
            heading("Haptic Motor Visualizer", size="4"),
            text(f"Status: {State.connection_status}"),
            hstack(
                rx.foreach(
                    range(10),
                    lambda i: motor_circle(i, State.motor_values[i])
                ),
                wrap="wrap",
                justify="center",
            ),
            button(
                "Start BLE Connection",
                on_click=lambda: threading.Thread(target=run_ble_client, daemon=True).start(),
                color_scheme="blue",
                is_disabled=State.connection_status != "Disconnected",
            ),
            width="100%",
            spacing="4",
            padding="2em",
        ),
        width="100%",
    )


# Create the app
app = rx.App()
app.add_page(index)


# For manual testing without actual BLE device
def dev_test_values():
    """Function to manually test UI updates without BLE."""
    import random
    import time
    
    while True:
        # Generate random values
        random_values = [random.randint(0, 255) for _ in range(10)]
        State.update_motors(State, random_values)
        time.sleep(1)


# Uncomment for development testing without actual BLE device
# threading.Thread(target=dev_test_values, daemon=True).start()


# Entry point
if __name__ == "__main__":
    app.compile()