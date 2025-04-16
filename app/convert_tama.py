from PIL import Image

# Adjust these as needed
TARGET_WIDTH = 16
TARGET_HEIGHT = 16

# Define your "dark blue" color range in RGB.
# For instance, if the outline is (0, 0, 128) or something similar,
# set a threshold to decide which pixels count as "dark blue."
DARK_BLUE_THRESHOLD = (60, 60, 100)  # example threshold


def is_dark_blue(rgb):
    r, g, b = rgb
    # We'll say it's "dark blue" if it's below these thresholds in R/G,
    # and 'b' is somewhat higher than 60
    return (r < DARK_BLUE_THRESHOLD[0] and
            g < DARK_BLUE_THRESHOLD[1] and
            b > DARK_BLUE_THRESHOLD[2])


def main():
    # 1. Load the image
    img = Image.open("static/tama.png").convert("RGB")

    # 2. Resize if needed
    # If your image is already the correct pixel size, you can skip resizing
    img = img.resize((TARGET_WIDTH, TARGET_HEIGHT), Image.NEAREST)

    # 3. Convert to a 2D array
    pixel_data = []
    for y in range(TARGET_HEIGHT):
        row = []
        for x in range(TARGET_WIDTH):
            r, g, b = img.getpixel((x, y))

            # If it's "dark blue," we assign 1, else 0
            if is_dark_blue((r, g, b)):
                row.append(1)
            else:
                row.append(0)
        pixel_data.append(row)

    # 4. Print out a JavaScript-friendly 2D array
    print("const tamagotchiPattern = [")
    for row in pixel_data:
        print("    [{}],".format(",".join(str(val) for val in row)))
    print("];")


if __name__ == "__main__":
    main()