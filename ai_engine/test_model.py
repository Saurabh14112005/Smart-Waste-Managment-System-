import os
import argparse
import time
from PIL import Image

# Suppress TF warnings
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"

from classifier import classifier

def main(image_path: str):
    if not os.path.exists(image_path):
        print(f"❌ Error: Image '{image_path}' not found.")
        return

    print(f"🔍 Testing Image: {image_path}")
    try:
        img = Image.open(image_path)
    except Exception as e:
        print(f"❌ Error opening image: {e}")
        return

    print("⏳ Running Inference...")
    label, conf, guide, timing = classifier.predict(img)

    print("\n" + "="*40)
    print("🧠 AI ANALYSIS RESULTS")
    print("="*40)
    if label == "Engine Offline":
        print("⚠️ ENGINE OFFLINE: Model 'waste_model.h5' is missing from 'models/' folder.")
        print("💡 Tip: Use 'train_model.py' to generate one, or place a pre-trained model there.")
    else:
        print(f"🏷️  Class     : {label}")
        print(f"🎯 Confidence: {conf*100:.1f}%")
        print(f"♻️  Guidance  : {guide}")
        print(f"⚡ Speed     : {timing}ms")
    print("="*40)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Test Waste Classification Model locally")
    parser.add_argument("image", type=str, help="Path to the image to classify")
    args = parser.parse_args()
    
    main(args.image)
