from PIL import Image, ImageDraw, ImageFont
import os

# Create a new image with a white background
width = 500
height = 500
image = Image.new('RGB', (width, height), 'white')
draw = ImageDraw.Draw(image)

# Draw a circle
circle_radius = 200
circle_center = (width // 2, height // 2)
draw.ellipse(
    [
        circle_center[0] - circle_radius,
        circle_center[1] - circle_radius,
        circle_center[0] + circle_radius,
        circle_center[1] + circle_radius
    ],
    outline='navy',
    width=10
)

# Add text
try:
    # Try to use a default system font
    font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 60)
except:
    # If the system font is not available, use default font
    font = ImageFont.load_default()

text = "CEIA"
# Get the size of the text
text_bbox = draw.textbbox((0, 0), text, font=font)
text_width = text_bbox[2] - text_bbox[0]
text_height = text_bbox[3] - text_bbox[1]

# Calculate position to center the text
text_x = (width - text_width) // 2
text_y = (height - text_height) // 2

# Draw the text
draw.text((text_x, text_y), text, font=font, fill='navy')

# Save the image
image.save('static/logo.png')
