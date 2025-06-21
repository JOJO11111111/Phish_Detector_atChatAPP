#!/usr/bin/env python3
"""
Start the Phishing Detection Backend Service
"""

import os
import sys
from app import app

if __name__ == '__main__':
    print("Starting Phishing Detection Backend Service...")
    print("Service will be available at: http://localhost:5000")
    print("Press Ctrl+C to stop the service")
    
    # Create necessary directories
    os.makedirs('./datasets/deployment', exist_ok=True)
    os.makedirs('./results/deployment', exist_ok=True)
    
    # Start the Flask app
    app.run(host='0.0.0.0', port=5000, debug=True) 