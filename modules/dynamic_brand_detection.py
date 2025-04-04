# dynamic_brand_detection.py


import base64
import io
from PIL import Image
from openai import OpenAI
from tldextract import tldextract
import pickle

class DynamicBrandDetector:
    def __init__(self, api_key, domain_map_path=None):
        # Initialize the OpenAI client
        self.client = OpenAI(api_key=api_key)
        self.domain_map = {}
        if domain_map_path:
            with open(domain_map_path, 'rb') as handle:
                self.domain_map = pickle.load(handle)
        
    def analyze_logo(self, image_path, logo_boxes=None):
        """Analyze logo using GPT-4o Vision API
        
        Args:
            image_path: Path to the screenshot
            logo_boxes: Optional list of logo bounding boxes. If provided, will extract and analyze logos individually
        """
        try:
            if logo_boxes is None or len(logo_boxes) == 0:
                # Full image analysis if no logo boxes provided
                image = Image.open(image_path)
                img_byte_arr = io.BytesIO()
                image.save(img_byte_arr, format='PNG')
                img_byte_arr = img_byte_arr.getvalue()
                img_base64 = base64.b64encode(img_byte_arr).decode('utf-8')
                
                messages = [
                    {"role": "system", "content": "You are an expert in identifying brand logos. Return only the brand name without explanation."},
                    {"role": "user", "content": [
                        {"type": "text", "text": (
                            "What brand logo is shown in this image? Respond with just the brand name, no explanation. "
                            "For example: 'PayPal', 'Amazon', 'Google', etc. "
                            "If you can't identify a specific brand, respond with 'None'."
                        )},
                        {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{img_base64}"}}
                    ]}
                ]
                
                response = self.client.chat.completions.create(
                    model="gpt-4o",
                    messages=messages,
                    max_tokens=50
                )
                
                result = response.choices[0].message.content.strip()
                return result if result.lower() != "None" else None
            
            else:
                # Analyze each logo box
                full_image = Image.open(image_path)
                
                for box in logo_boxes:
                    # Extract logo from the box
                    cropped = full_image.crop((box[0], box[1], box[2], box[3]))
                    
                    # Convert to base64
                    img_byte_arr = io.BytesIO()
                    cropped.save(img_byte_arr, format='PNG')
                    img_byte_arr = img_byte_arr.getvalue()
                    img_base64 = base64.b64encode(img_byte_arr).decode('utf-8')
                    
                    # Prompt for this specific logo
                    messages = [
                        {"role": "system", "content": "You are an expert in identifying brand logos. Return only the brand name without explanation."},
                        {"role": "user", "content": [
                            {"type": "text", "text": (
                                "Identify this brand logo. Respond with just the brand name, no explanation. "
                                "For example: 'PayPal', 'Amazon', 'Google', etc. "
                                "If you can't identify a specific brand, respond with 'None'."
                            )},
                            {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{img_base64}"}}
                        ]}
                    ]
                    
                    response = self.client.chat.completions.create(
                        model="gpt-4o",
                        messages=messages,
                        max_tokens=50
                    )
                    
                    result = response.choices[0].message.content.strip()
                    if result.lower() != "None":
                        return result
                
                # If no logo was identified from any box
                return None
            
        except Exception as e:
            print(f"Error analyzing logo: {e}")
            return None
    
    def get_expected_domains(self, brand_name):
        """Get expected domains for a given brand"""
        # Try to find in the domain map first
        if brand_name.lower() in self.domain_map:
            return self.domain_map[brand_name.lower()]
        
        # If no match, create a simple guess based on brand name
        brand_as_domain = brand_name.lower().replace(' ', '')
        return [f"{brand_as_domain}.com"]
    
    def is_domain_consistent(self, brand_name, url):
        """Check if URL's domain is consistent with the expected domain for the brand"""
        if not brand_name:
            return False
        
        # Extract domain from URL
        extracted = tldextract.extract(url)
        current_domain = extracted.domain
        
        # Get expected domains for the brand
        expected_domains = self.get_expected_domains(brand_name)
        
        # Check if current domain matches any expected domain
        for domain in expected_domains:
            extracted_expected = tldextract.extract(domain)
            if current_domain == extracted_expected.domain:
                return True
        
        return False