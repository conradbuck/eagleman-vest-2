import matplotlib.pyplot as plt
import numpy as np

# custom haptic motor colors
COLORS = [
    (57, 252, 3), (65, 181, 129), (65, 250, 228), (247, 173, 255), (40, 119, 209),
    (232, 32, 76), (255, 183, 3), (226, 237, 173), (60, 60, 145), (156, 11, 71)
]
COLORS = [(r/255, g/255, b/255) for r, g, b in COLORS]

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


joint_angles = [np.pi/3, -np.pi/2, 0.7, -1.0]
motor_values = [20, 80, 150, 255, 190, 60, 30, 210, 100, 245]
draw_combined_visual(joint_angles, motor_values)
