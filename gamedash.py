import pygame
import time
from ntcore import NetworkTableInstance
import sys
import pygame.mixer
import os

# Initialize Pygame and Pygame mixer for sound
pygame.init()
pygame.mixer.init()

# Function to safely load a sound file with error handling
def load_sound(file_path):
    if os.path.exists(file_path):
        try:
            return pygame.mixer.Sound(file_path)
        except pygame.error as e:
            print(f"Error loading sound file {file_path}: {e}")
            return None
    else:
        print(f"Sound file {file_path} not found.")
        return None

# Load chime sounds with error handling for missing files
chime1 = load_sound('chime1.mp3')
chime2 = load_sound('chime2.mp3')
chime3 = load_sound('chime3.mp3')

# Get display size
display_info = pygame.display.Info()
screen_width = display_info.current_w - 100
screen_height = display_info.current_h // 2

# Set up the window
screen = pygame.display.set_mode((screen_width, screen_height))
pygame.display.set_caption("FRC Dashboard")

# Set up NetworkTables using the publish-subscribe model
ntinst = NetworkTableInstance.getDefault()
ntinst.setServer("127.0.0.1")  # Set the server to the local robot's IP (127.0.0.1)
ntinst.startClient4("FRC_Dashboard")  # Start client with a specific identity

# Get the telemetry table
telemetry_table = ntinst.getTable("telemetry")
fms_info_table = ntinst.getTable("FMSInfo")  # For FMSControlData

# Subscribe to telemetry data
ds_r_entry = telemetry_table.getIntegerTopic("DS_R").subscribe(0)
ds_g_entry = telemetry_table.getIntegerTopic("DS_G").subscribe(0)
ds_b_entry = telemetry_table.getIntegerTopic("DS_B").subscribe(0)
ds_largetext_entry = telemetry_table.getStringTopic("DS_largetext").subscribe("")
ds_smalltext_entry = telemetry_table.getStringTopic("DS_smalltext").subscribe("")
ds_largetext_flash_entry = telemetry_table.getBooleanTopic("DS_largetext_flash").subscribe(False)
ds_smalltext_flash_entry = telemetry_table.getBooleanTopic("DS_smalltext_flash").subscribe(False)

# Subscribe to FMSControlData
fms_control_data_entry = fms_info_table.getIntegerTopic("FMSControlData").subscribe(0)

# Subscribe to chime boolean variables
ds_chime_1_entry = telemetry_table.getBooleanTopic("DS_chime_1").subscribe(False)
ds_chime_2_entry = telemetry_table.getBooleanTopic("DS_chime_2").subscribe(False)
ds_chime_3_entry = telemetry_table.getBooleanTopic("DS_chime_3").subscribe(False)

# Edge settings
edge_width = 50

# Flash intervals
flash_interval = 0.25  # Seconds

# FMSControlData color mappings and FMS attached logic
def get_fms_edge_color(fms_control_data):
    fms_attached_colors = {
        48: (255, 0, 0),   # Red for Disabled
        49: (0, 255, 0),   # Green for Teleop
        51: (0, 0, 255),   # Blue for Auto
        53: (255, 255, 0)  # Yellow for Test
    }
    fms_not_attached_colors = {
        32: (255, 0, 0),   # Red for Disabled
        33: (0, 255, 0),   # Green for Teleop
        35: (0, 0, 255),   # Blue for Auto
        37: (255, 255, 0)  # Yellow for Test
    }
    if fms_control_data in fms_attached_colors:
        return fms_attached_colors[fms_control_data], True  # True means FMS is attached
    elif fms_control_data in fms_not_attached_colors:
        return fms_not_attached_colors[fms_control_data], False  # False means FMS is not attached
    else:
        return (169, 169, 169), False  # Grey for disconnected or unknown

# Function to draw text with optional flashing
def draw_text(screen, text, font, color, center_position, flash, elapsed_time):
    if not flash or int(elapsed_time / flash_interval) % 2 == 0:
        text_surface = font.render(text, True, color)
        text_rect = text_surface.get_rect(center=center_position)
        screen.blit(text_surface, text_rect)

# Function to invert the color
def invert_color(r, g, b):
    return (255 - r, 255 - g, 255 - b)

# Function to dynamically adjust font size based on text length and available space
def get_dynamic_font(text, max_width, max_height, base_font_size):
    font_size = base_font_size
    font = pygame.font.Font(None, font_size)
    text_surface = font.render(text, True, (0, 0, 0))
    text_width, text_height = text_surface.get_size()

    # Adjust font size based on width and height constraints
    while text_width > max_width or text_height > max_height:
        font_size -= 1
        font = pygame.font.Font(None, font_size)
        text_surface = font.render(text, True, (0, 0, 0))
        text_width, text_height = text_surface.get_size()

    return font

# Latch state for chime playback
chime1_played = False
chime2_played = False
chime3_playing = False  # State for looping chime 3

# Main loop
running = True
clock = pygame.time.Clock()
start_time = time.time()

while running:
    elapsed_time = time.time() - start_time

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    # Get canvas color from NetworkTables
    ds_r = ds_r_entry.get()
    ds_g = ds_g_entry.get()
    ds_b = ds_b_entry.get()
    canvas_color = (ds_r, ds_g, ds_b)
    text_color = invert_color(ds_r, ds_g, ds_b)

    # Get FMSControlData
    fms_control_data = fms_control_data_entry.get()

    # Determine the edge color and if FMS is attached
    edge_color, fms_attached = get_fms_edge_color(fms_control_data)

    # Get text data
    ds_largetext = ds_largetext_entry.get()
    ds_smalltext = ds_smalltext_entry.get()

    # Get flash data
    largetext_flash = ds_largetext_flash_entry.get()
    smalltext_flash = ds_smalltext_flash_entry.get()

    # Get chime states
    chime1_trigger = ds_chime_1_entry.get()
    chime2_trigger = ds_chime_2_entry.get()
    chime3_trigger = ds_chime_3_entry.get()

    # Handle chime playback with latching (Chime 1 and 2) and looping (Chime 3)
    
    # Chime 1 (Latched)
    if chime1_trigger and not chime1_played and chime1:
        chime1.play()
        chime1_played = True
    elif not chime1_trigger:
        chime1_played = False  # Reset latch

    # Chime 2 (Latched)
    if chime2_trigger and not chime2_played and chime2:
        chime2.play()
        chime2_played = True
    elif not chime2_trigger:
        chime2_played = False  # Reset latch

    # Chime 3 (Looping)
    if chime3_trigger and chime3 and not chime3_playing:
        chime3.play(loops=-1)  # Start looping Chime 3
        chime3_playing = True
    elif not chime3_trigger and chime3_playing:
        chime3.stop()  # Stop Chime 3 immediately
        chime3_playing = False

    # Fill the screen with the canvas color
    screen.fill(canvas_color)

    # Dynamically determine font size based on available canvas space
    available_width = screen_width - 2 * edge_width
    available_height = screen_height - 2 * edge_width

    # Get dynamic font for large and small text
    large_font = get_dynamic_font(ds_largetext, available_width, available_height // 2, 200)
    small_font = get_dynamic_font(ds_smalltext, available_width, available_height // 4, 100)

    # Render large text in the center of the screen
    draw_text(screen, ds_largetext, large_font, text_color, (screen_width // 2, screen_height // 2 - 50), largetext_flash, elapsed_time)
    
    # Render small text just below the large text
    draw_text(screen, ds_smalltext, small_font, text_color, (screen_width // 2, screen_height // 2 + 50), smalltext_flash, elapsed_time)

    # Draw the colored edge based on FMSControlData
    pygame.draw.rect(screen, edge_color, (0, 0, screen_width, edge_width))  # Top edge
    pygame.draw.rect(screen, edge_color, (0, screen_height - edge_width, screen_width, edge_width))  # Bottom edge
    pygame.draw.rect(screen, edge_color, (0, 0, edge_width, screen_height))  # Left edge
    pygame.draw.rect(screen, edge_color, (screen_width - edge_width, 0, edge_width, screen_height))  # Right edge

    # If FMS is attached, display "FMS Connected" on the bottom edge
    if fms_attached:
        font = pygame.font.Font(None, 36)
        text_surface = font.render("FMS Connected", True, (255, 255, 255))  # White text
        text_rect = text_surface.get_rect(center=(screen_width // 2, screen_height - edge_width // 2))
        screen.blit(text_surface, text_rect)

    # Update the display
    pygame.display.flip()

    # Flush NetworkTables to ensure data is sent/received
    ntinst.flush()

    # Limit the frame rate
    clock.tick(60)

# Clean up
pygame.quit()
sys.exit()