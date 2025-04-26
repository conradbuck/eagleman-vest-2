import asyncio
from bleak import BleakClient, BleakScanner
import serial
import argparse
import json
import matplotlib.pyplot as plt
import numpy as np

# Global figure and axes creation (one-time setup)
fig = plt.figure(figsize=(14, 7))
gs = fig.add_gridspec(2, 4, height_ratios=[2, 1])  # Create 4 columns for joint angle gauges
ax_row1 = [fig.add_subplot(gs[0, i], projection='polar') for i in range(4)]  # 4 subplots in the first row
ax_haptics = fig.add_subplot(gs[1, :])  # Single subplot for haptic motor feedback (spans all columns)

# Turn on interactive mode
plt.ion()

# Set up the plot only once
ax_haptics.set_xlim(0, 10)
ax_haptics.set_ylim(0, 1)
ax_haptics.axis('off')
ax_haptics.set_title("Haptic Motor Feedback", fontsize=14)

# Define the colors and other settings you may want to use
COLORS = ["#39fc03", "#41b581", "#41fae4", "#f7adff", "#2877d1", "#e8204c", "#ffb703", "#e2edad", "#3c3c91", "#9c0b47"]
BACKGROUND = "#ffeccf"


# UUIDs
SERVICE_UUID_2 = "87654321-4321-4321-4321-0987654321ba"
CHARACTERISTIC_UUID_2 = "fedcbafe-4321-8765-4321-fedcbafedcba"

# ESP32 advertised name
DEVICE_NAME_2 = "ESP32_Receiver"

# Global serial object
ser = None

# Global angles
base_angle = 0.0
shoulder_angle = 0.0
elbow_angle = 1.57
hand_angle = 3.14

# For detecting changes
prev_base = None
prev_shoulder = None
prev_elbow = None
prev_hand = None

MIN_ANGLE = -3.14
MAX_ANGLE = 3.14
# Visualization function
def draw_combined_visual(joint_angles_rad, motor_values):
    """
    Draws 4 joint angle radian gauges and 10 haptic motor feedback circles.
    
    Args:
        joint_angles_rad (list of float): 4 values in radians (-π to π)
        motor_values (list of int): 10 values between 1–255.
    """
    if len(joint_angles_rad) != 4:
        raise ValueError("Please provide 4 joint angles (radians).")
    if len(motor_values) != 10:
        raise ValueError("Please provide 10 haptic motor values (1–255).")

    # --- Update the 4 Joint Angle Gauges ---
    for i, (ax, angle) in enumerate(zip(ax_row1, joint_angles_rad)):
        ax.clear()
        ax.set_theta_zero_location('N')
        ax.set_theta_direction(-1)
        ax.set_rticks([])
        ax.set_xticks(np.linspace(-np.pi, np.pi, 5))
        ax.set_xticklabels([r"$-\pi$", r"$-\frac{\pi}{2}$", "0", r"$\frac{\pi}{2}$", r"$\pi$"])

        # Background arc
        ax.bar(np.linspace(-np.pi, np.pi, 100), [1]*100, width=0.06, color='#eee', alpha=0.3)
        # Current angle
        ax.bar([angle], [1], width=0.15, color='C0')
        ax.set_title(f"Joint {i+1}\n{angle:.2f} rad", va='bottom')

    # --- Update the 10 Haptic Motor Circles ---
    ax_haptics.clear()  # Clear the existing motor circle plot
    ax_haptics.set_xlim(0, 10)
    ax_haptics.set_ylim(0, 1)
    ax_haptics.axis('off')
    ax_haptics.set_title("Haptic Motor Feedback", fontsize=14)

    for i, (val, color) in enumerate(zip(motor_values, COLORS)):
        radius = 0.1 + (val / 255.0) * 0.3
        circle = plt.Circle((i + 0.5, 0.5), radius, color=color)
        ax_haptics.add_patch(circle)
        ax_haptics.text(i + 0.5, 0.05, f"{val}", ha='center', va='center', fontsize=9)

    # Redraw the plot and pause for a brief moment to allow for updates
    plt.draw()  
    plt.pause(0.001)  # Short pause to allow updates without blocking


async def send_robot_commands():
    global base_angle, shoulder_angle, elbow_angle, hand_angle
    global prev_base, prev_shoulder, prev_elbow, prev_hand

    while True:
        if (base_angle != prev_base or
            shoulder_angle != prev_shoulder or
            elbow_angle != prev_elbow or
            hand_angle != prev_hand):

            command = {
                "T": 102,
                "base": base_angle,
                "shoulder": shoulder_angle,
                "elbow": elbow_angle,
                "hand": hand_angle,
                "spd": 10,
                "acc": 10
            }

            ser.write((json.dumps(command) + "\n").encode())
            print(f"Sent robot command: {command}")

            prev_base = base_angle
            prev_shoulder = shoulder_angle
            prev_elbow = elbow_angle
            prev_hand = hand_angle

        await asyncio.sleep(0.1)

async def keyboard_control():
    import sys
    import termios
    import tty

    global base_angle, shoulder_angle, elbow_angle, hand_angle

    def getch():
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        try:
            tty.setraw(sys.stdin.fileno())
            ch = sys.stdin.read(1)
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
        return ch

    print("Keyboard control active (W/S: Shoulder, A/D: Base, Q/E: Elbow, T/G: Hand)")

    while True:
        key = await asyncio.to_thread(getch)
        step = 0.3  # radians

        if key.lower() == 'w':
            shoulder_angle = min(shoulder_angle + step, MAX_ANGLE)
            print(f"Shoulder up: {shoulder_angle:.2f}")
        elif key.lower() == 's':
            shoulder_angle = max(shoulder_angle - step, MIN_ANGLE)
            print(f"Shoulder down: {shoulder_angle:.2f}")
        elif key.lower() == 'a':
            base_angle = max(base_angle - step, MIN_ANGLE)
            print(f"Base rotate left: {base_angle:.2f}")
        elif key.lower() == 'd':
            base_angle = min(base_angle + step, MAX_ANGLE)
            print(f"Base rotate right: {base_angle:.2f}")
        elif key.lower() == 'q':
            elbow_angle = min(elbow_angle + step, MAX_ANGLE)
            print(f"Elbow up: {elbow_angle:.2f}")
        elif key.lower() == 'e':
            elbow_angle = max(elbow_angle - step, MIN_ANGLE)
            print(f"Elbow down: {elbow_angle:.2f}")
        elif key.lower() == 't':
            hand_angle = min(hand_angle + step, MAX_ANGLE)
            print(f"Hand rotate open: {hand_angle:.2f}")
        elif key.lower() == 'g':
            hand_angle = max(hand_angle - step, MIN_ANGLE)
            print(f"Hand rotate close: {hand_angle:.2f}")
        elif key.lower() == 'x':
            print("Exiting keyboard control...")
            break

        await asyncio.sleep(0.05)

async def send_continuous_commands(client2):
    global base_angle, shoulder_angle, elbow_angle, hand_angle

    while True:
        def map_angle_to_byte(angle):
            value = int(255 * (angle - MIN_ANGLE) / (MAX_ANGLE - MIN_ANGLE))
            return 254 if value == 0xAA else value

        bytes_to_send = [
            map_angle_to_byte(-base_angle),
            map_angle_to_byte(base_angle),
            map_angle_to_byte(-shoulder_angle),
            map_angle_to_byte(shoulder_angle),
            map_angle_to_byte(-elbow_angle),
            map_angle_to_byte(elbow_angle),
            map_angle_to_byte(-hand_angle),
            map_angle_to_byte(hand_angle),
            0,
            0
        ]
        draw_combined_visual([base_angle, shoulder_angle, elbow_angle, hand_angle], bytes_to_send)
        framed_data = bytes([0xAA] + bytes_to_send)
        await client2.write_gatt_char(CHARACTERISTIC_UUID_2, framed_data)
        print(f"Continuously sent: {[hex(b) for b in framed_data]}")

        await asyncio.sleep(0.1)

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

        # Start robot serial command loop
        asyncio.create_task(send_robot_commands())

        # Start keyboard control loop
        asyncio.create_task(keyboard_control())

        # Start continuous BLE command loop
        asyncio.create_task(send_continuous_commands(client2))

        while True:
            await asyncio.sleep(1)

async def main():
    global ser

    parser = argparse.ArgumentParser(description='Serial JSON Communication')
    parser.add_argument('port', type=str, help='Serial port name (e.g., COM1 or /dev/ttyUSB0)')
    args = parser.parse_args()

    ser = serial.Serial(args.port, baudrate=115200)
    ser.setRTS(False)
    ser.setDTR(False)

    await send_user_commands()

if __name__ == "__main__":
    asyncio.run(main())
