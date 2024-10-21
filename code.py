import board
import busio
import digitalio
import displayio
import math
import rgbmatrix
import framebufferio
import time
import gifio
import os
import gc
from adafruit_debouncer import Debouncer
import adafruit_lis3dh

# Get a dictionary of GIF filenames at the passed base directory
def get_files(base):
    allfiles = os.listdir(base)
    file_names = []
    for _, filetext in enumerate(allfiles):
        if not filetext.startswith("."):
            if filetext not in ('boot_out.txt', 'System Volume Information'):
                if filetext.endswith(".gif"):
                    file_names.append(filetext)
    return sorted(file_names)

# Configure buttons
button_update_interval = 0.01
up_pin = digitalio.DigitalInOut(board.BUTTON_UP)
down_pin = digitalio.DigitalInOut(board.BUTTON_DOWN)
up_pin.direction = digitalio.Direction.INPUT
down_pin.direction = digitalio.Direction.INPUT
up_pin.pull = digitalio.Pull.UP
down_pin.pull = digitalio.Pull.UP
up_button = Debouncer(up_pin)
down_button = Debouncer(down_pin)

# Set for 1 matrix
bit_depth = 6
base_width = 64
base_height = 32
chain_across = 1
tile_down = 1
serpentine = True

width = base_width * chain_across
height = base_height * tile_down

addr_pins = [board.MTX_ADDRA, board.MTX_ADDRB, board.MTX_ADDRC, board.MTX_ADDRD]
rgb_pins = [
    board.MTX_R1,
    board.MTX_G1,
    board.MTX_B1,
    board.MTX_R2,
    board.MTX_G2,
    board.MTX_B2,
]
clock_pin = board.MTX_CLK
latch_pin = board.MTX_LAT
oe_pin = board.MTX_OE

displayio.release_displays()
matrix = rgbmatrix.RGBMatrix(
                width=width,
                height=height,
                bit_depth=bit_depth,
                rgb_pins=rgb_pins,
                addr_pins=addr_pins,
                clock_pin=clock_pin,
                latch_pin=latch_pin,
                output_enable_pin=oe_pin,
                tile=tile_down,
                serpentine=serpentine,
            )
display = framebufferio.FramebufferDisplay(matrix)

# figure out display orientation
accelerometer = adafruit_lis3dh.LIS3DH_I2C(busio.I2C(board.SCL, board.SDA), address=0x19)
# flush initial reading
_ = accelerometer.acceleration
# wait for new reading
time.sleep(button_update_interval)
def update_rotation():
    # read accel
    current_accel = accelerometer.acceleration
    # determine rotation
    new_rotation = (int(((math.atan2(-current_accel.y, -current_accel.x) + math.pi) / (math.pi * 2) + 0.875) * 2) % 2) * 180
    # update if necessary
    if new_rotation != display.rotation:
        display.rotation = new_rotation
update_rotation()

splash = displayio.Group()
display.root_group = splash

DIRECTORY = "/gifs/"

files = get_files(DIRECTORY)
gif_index = 0
# Loop forever
while True:
    # Update buttons (in case one was just released)
    up_button.update()
    down_button.update()
    # Load the gif
    odg = gifio.OnDiskGif(DIRECTORY+files[gif_index])
    # Load the first frame (and track how long it takes)
    start = time.monotonic()
    next_delay = odg.next_frame()
    end = time.monotonic()
    overhead = end - start # how long did loading a frame take
    # Create a TileGrid object containing the gif's bitmap
    gif_tile = displayio.TileGrid(
        odg.bitmap,
        pixel_shader=displayio.ColorConverter(
            input_colorspace=displayio.Colorspace.RGB565_SWAPPED
        ),
    )
    # Append it to the splash Group
    splash.append(gif_tile)
    # Display the GIF until a button is pressed and released
    while not up_button.rose and not down_button.rose:
        # time at which this frame started (seconds)
        frame_shown = time.monotonic()
        # update the display (for some reason this has to happen before loading the next frame)
        display.refresh()
        # move to next frame and get delay (seconds) before the following one
        next_delay = odg.next_frame()
        # update rotation if needed
        update_rotation()
        # measure overhead again
        overhead = time.monotonic() - frame_shown
        # we're currently already this far in to the frame display
        current_delay = overhead
        # we want to poll buttons and sleep until we're this far in
        target_delay = next_delay - overhead
        # until the delay is equal to the target, we keep sleeping for 0.01s
        while current_delay < target_delay:
            # poll button positions
            up_button.update()
            down_button.update()
            # handle next file (up button)
            if up_button.rose:
                gif_index += 1
                if gif_index >= len(files):
                    gif_index = 0
                break
            # handle prev file (down button)
            if down_button.rose:
                gif_index -= 1
                if gif_index < 0:
                    gif_index = len(files) - 1
                break
            # if we're past the target time, sleep 0 seconds.  otherwise sleep 0.01 or the target (if that's somehow less than 0.01s)
            time.sleep(min(button_update_interval, max(0, target_delay)))
            current_delay = time.monotonic() - frame_shown
    splash.remove(gif_tile)
