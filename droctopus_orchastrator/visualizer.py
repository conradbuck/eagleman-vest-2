import asyncio
from bleak import BleakClient, BleakScanner
import matplotlib.pyplot as plt

# UUIDs (same as before)
SERVICE_UUID_2 = "87654321-4321-4321-4321-0987654321ba"
CHARACTERISTIC_UUID_2 = "fedcbafe-4321-8765-4321-fedcbafedcba"

# ESP32 advertised name
DEVICE_NAME_2 = "ESP32_Receiver"

# Generate unique colors for each motor
COLORS = [(57, 252, 3), (65, 181, 129), (65, 250, 228), (247, 173, 255), (40, 119, 209), (232, 32, 76), (255, 183, 3), (226, 237, 173), (60, 60, 145), (156, 11, 71)]
BACKGROUND = (255, 236, 207)


# Visualization function
def draw_combined_visual(joint_angles_rad, motor_values):
    """
    Draws 4 joint angle radian gauges and 10 haptic motor feedback circles.
    
    Args:
        joint_angles_rad (list of float): 4 values in radians (-π to π)
        motor_values (list of int): 10 values between 1–255
    """
    if len(joint_angles_rad) != 4:
        raise ValueError("Please provide 4 joint angles (radians).")
    if len(motor_values) != 10:
        raise ValueError("Please provide 10 haptic motor values (1–255).")

    fig = plt.figure(figsize=(14, 7))
    gs = fig.add_gridspec(2, 1, height_ratios=[2, 1])

    # --- Top: 4 Joint Angle Gauges ---
    ax_row1 = [fig.add_subplot(gs[0], projection='polar') for _ in range(4)]
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

    # --- Bottom: 10 Haptic Motor Circles ---
    ax_haptics = fig.add_subplot(gs[1])
    ax_haptics.set_xlim(0, 10)
    ax_haptics.set_ylim(0, 1)
    ax_haptics.axis('off')
    ax_haptics.set_title("Haptic Motor Feedback", fontsize=14)

    for i, (val, color) in enumerate(zip(motor_values, COLORS)):
        radius = 0.1 + (val / 255.0) * 0.3
        circle = plt.Circle((i + 0.5, 0.5), radius, color=color)
        ax_haptics.add_patch(circle)
        ax_haptics.text(i + 0.5, 0.05, f"{val}", ha='center', va='center', fontsize=9)

    plt.tight_layout()
    plt.show()



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
        
        # Initialize with zeros
        byte_values = [0] * 10
        visualization_active = draw_combined_visual([0,0,0,0,], byte_values)
        
        while visualization_active:
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
                
                # Update visualization
                visualization_active = draw_combined_visual([0,0,0,0], byte_values)
                if not visualization_active:
                    break
                
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