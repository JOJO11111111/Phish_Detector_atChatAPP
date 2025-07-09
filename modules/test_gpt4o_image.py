import base64
import io
from PIL import Image
from openai import OpenAI

# Initialize the OpenAI client
from config import OPENAI_API_KEY
client = OpenAI(api_key=OPENAI_API_KEY)  # API key loaded from configey

def encode_image_to_base64(image_path):
    """Convert an image to a base64-encoded string."""
    with Image.open(image_path) as img:
        # Convert image to PNG format
        img_byte_arr = io.BytesIO()
        img.save(img_byte_arr, format="PNG")
        img_byte_arr = img_byte_arr.getvalue()
        # Encode to base64
        img_base64 = base64.b64encode(img_byte_arr).decode("utf-8")
        return img_base64

def analyze_logo(image_path):
    """Send the image to GPT-4o and ask for the brand's domain."""
    try:
        # Encode the image
        img_base64 = encode_image_to_base64(image_path)

        # Construct the messages list
        messages = [
            {"role": "system", "content": "You are an expert in brand logos."},
            {"role": "user", "content": [
                {"type": "text", "text": (
                    "Given the attached logo image, decide the brand's domain in English. "
                    "Return only the domain name with no explanation. "
                    "If there are multiple possibilities, choose the most likely one."
                )},
                {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{img_base64}"}}  # Fix: Use an object for `image_url`
            ]}
        ]

        # Call the OpenAI API
        response = client.chat.completions.create(
            model="gpt-4o",  # Use the correct model name
            messages=messages,
            max_tokens=50
        )

        # Extract and return the response
        result = response.choices[0].message.content.strip()
        return result

    except Exception as e:
        print(f"Error analyzing logo: {e}")
        return None


# Test the function with multiple image paths
if __name__ == "__main__":
    # List of image paths to analyze
    image_paths = [
        "/home/tiffanybao/PhishIntention/datasets/test_sites/tiffanyWebsite.app/shot.png",
        "/home/tiffanybao/PhishIntention/datasets/test_sites/accounts.g.cdcde.com/shot.png",  # Add more paths here
    ]

    # Loop through each image and analyze it
    for image_path in image_paths:
        print(f"Analyzing logo: {image_path}")
        brand_domain = analyze_logo(image_path)
        if brand_domain:
            print(f"Detected brand domain: {brand_domain}")
        else:
            print("No brand detected.")
        print("-" * 40)  # Separator for readability