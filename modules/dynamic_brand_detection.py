import base64
import io
from PIL import Image
from openai import OpenAI  # Import the OpenAI client

class DynamicBrandDetector:
    def __init__(self, api_key):
        # Initialize the OpenAI client
        self.client = OpenAI(api_key=api_key)
        
    def analyze_logo(self, image_path):
        """Analyze logo using GPT-4 Vision API"""
        try:
            # Open and prepare image
            image = Image.open(image_path)
            # Convert to PNG format
            img_byte_arr = io.BytesIO()
            image.save(img_byte_arr, format='PNG')
            img_byte_arr = img_byte_arr.getvalue()
            # Encode image to base64
            img_base64 = base64.b64encode(img_byte_arr).decode('utf-8')
            
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
            
            # Call the OpenAI Chat Completion API
            response = self.client.chat.completions.create(
                model="gpt-4o",  # Use the correct model name for vision tasks
                messages=messages,
                max_tokens=50
            )
            
            result = response.choices[0].message.content.strip()
            return result
            
        except Exception as e:
            print(f"Error analyzing logo: {e}")
            return None