from PIL import Image, ImageDraw, ImageFont
import os

# Create icons directory if it doesn't exist
os.makedirs("icons", exist_ok=True)

# Create icons of different sizes
sizes = [16, 48, 128]

for size in sizes:
    # Create a new image with a blue background
    img = Image.new('RGB', (size, size), color=(0, 123, 255))
    draw = ImageDraw.Draw(img)
    
    # Try to add text if the icon is large enough
    if size >= 48:
        try:
            # Try to use a font, fall back to default if not available
            font_size = size // 4
            try:
                font = ImageFont.truetype("Arial", font_size)
            except:
                font = ImageFont.load_default()
                
            # Add text
            text = "PI"
            text_width, text_height = draw.textsize(text, font=font) if hasattr(draw, 'textsize') else (size//2, size//2)
            position = ((size - text_width) // 2, (size - text_height) // 2)
            draw.text(position, text, fill=(255, 255, 255), font=font)
        except:
            # If text fails, just draw a simple shape
            draw.rectangle([size//4, size//4, 3*size//4, 3*size//4], fill=(255, 255, 255))
    else:
        # For small icons, just draw a simple shape
        draw.rectangle([size//4, size//4, 3*size//4, 3*size//4], fill=(255, 255, 255))
    
    # Save the icon
    img.save(f"icons/icon{size}.png")

print("Icons created successfully!") 