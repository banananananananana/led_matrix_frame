import time
import argparse
from rpi_ws281x import PixelStrip, Color
import math

# LED strip configuration:
LED_COUNT = 15          # Number of LED pixels
LED_PIN = 18            # GPIO pin connected to the pixels (18 is PWM).
LED_FREQ_HZ = 800000    # LED signal frequency in hertz (usually 800kHz)
LED_DMA = 10            # DMA channel to use for generating signal (try 10)
LED_BRIGHTNESS = 25     # Set to 0 for darkest and 255 for brightest
LED_INVERT = False      # True to invert the signal (when using NPN transistor level shift)
LED_CHANNEL = 0         # Channel to use for controlling the LEDs

# Matrix dimensions
MATRIX_WIDTH = 5
MATRIX_HEIGHT = 3

# Central coordinates for LED 5 (middle of the matrix)
center_lat = 55.7438006
center_lon = 12.5282253

# Scale factor for the map
scale_factor = 1 / 36  # 1 cm corresponds to 36 units of distance

# LED colors for each person
LED_COLORS = {
    "Thor": Color(0, 255, 0),     # Green for Thor
    "Mira": Color(255, 0, 0),     # Red for Mira
    "Stefan": Color(0, 0, 255),   # Blue for Stefan
}

# Function to map (x, y) coordinates to LED index (corrected serpentine layout)
def matrix_to_index(x, y):
    if y % 2 == 0:  # Even rows (Row 0, Row 2 are right to left)
        return y * MATRIX_WIDTH + (MATRIX_WIDTH - 1 - x)
    else:  # Odd rows (Row 1 is left to right)
        return y * MATRIX_WIDTH + x

# Function to calculate the closest LED for a given GPS coordinate
def closest_led(lat, lon):
    # Convert the GPS coordinates to a matrix index
    lat_diff = lat - center_lat
    lon_diff = lon - center_lon

    # Calculate the position in cm based on scale
    x_cm = lon_diff / scale_factor
    y_cm = lat_diff / scale_factor

    # Map the cm coordinates to the matrix size (with an offset for the center of the matrix)
    x = round(x_cm + (MATRIX_WIDTH - 1) / 2)

    # Adjust the Y coordinate: increasing latitude should move you *up* the matrix (toward row 0)
    y = round((MATRIX_HEIGHT - 1) / 2 - y_cm)  # Flipping the Y-axis calculation

    # Ensure x and y are within matrix bounds
    x = max(0, min(MATRIX_WIDTH - 1, x))
    y = max(0, min(MATRIX_HEIGHT - 1, y))

    # Return the LED index
    return matrix_to_index(x, y)

# Function to light up a specific LED with a specific color
def light_led(strip, led_index, color):
    strip.setPixelColor(led_index, color)

# Function to clear the LEDs
def clear_leds(strip):
    for i in range(LED_COUNT):
        strip.setPixelColor(i, Color(0, 0, 0))  # Turn off all LEDs
    strip.show()

# Function to read the location from a file
def read_location_from_file(filename):
    try:
        with open(filename, 'r') as f:
            # Each line will have the format "Name: lat, lon"
            line = f.read().strip()
            # Split the line at the colon, and then at the comma
            name, coords = line.split(":")
            lat, lon = map(float, coords.split(","))
            return lat, lon
    except FileNotFoundError:
        print(f"File {filename} not found.")
        return None
    except ValueError:
        print(f"Error parsing data from file {filename}. Ensure it's in the correct format.")
        return None

def main():
    # Set up the LED strip
    strip = PixelStrip(LED_COUNT, LED_PIN, LED_FREQ_HZ, LED_DMA, LED_INVERT, LED_BRIGHTNESS, LED_CHANNEL)
    strip.begin()

    last_update_times = {}  # Track when each LED was last updated for alternating colors

    # Main loop to track and update locations
    while True:
        # Read the locations from the individual files
        locations = {}

        # Read coordinates for Thor
        thor_coords = read_location_from_file('thor_location.txt')
        if thor_coords:
            locations['Thor'] = thor_coords

        # Read coordinates for Stefan
        stefan_coords = read_location_from_file('stefan_location.txt')
        if stefan_coords:
            locations['Stefan'] = stefan_coords

        # Read coordinates for Mira
        mira_coords = read_location_from_file('mira_position.txt')
        if mira_coords:
            locations['Mira'] = mira_coords

        # Clear previous LED states
        clear_leds(strip)

        # Track LED positions for each person
        led_positions = {}

        for name, (lat, lon) in locations.items():
            led_index = closest_led(lat, lon)
            if led_index not in led_positions:
                led_positions[led_index] = []
            led_positions[led_index].append(name)

        # Light up the LEDs
        for led_index, people_at_location in led_positions.items():
            if len(people_at_location) == 1:
                # Single person, use their specific color
                light_led(strip, led_index, LED_COLORS[people_at_location[0]])
            else:
                # More than one person, alternate colors
                current_time = time.time()

                # If this LED hasn't been updated recently, start alternating colors
                if led_index not in last_update_times or current_time - last_update_times[led_index] >= 1:
                    # Store the last update time
                    last_update_times[led_index] = current_time

                # Cycle through the colors for this LED
                colors = [LED_COLORS[name] for name in people_at_location]
                color_index = int(current_time // 1) % len(colors)  # Alternates colors every second
                light_led(strip, led_index, colors[color_index])

        # Show the updates
        strip.show()

        # Wait for 5 seconds before checking the locations again
        time.sleep(5)

if __name__ == '__main__':
    main()
