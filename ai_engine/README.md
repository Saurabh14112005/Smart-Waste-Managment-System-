# AI Engine - CleanCity Smart Waste Management

This module powers the computer vision and intelligence layer of the Smart Waste Management system. It is designed to classify waste captured by the ESP32-CAM into one of four categories, ensuring proper segregation.

## Features (Hackathon Ready 🚀)
- **Live Inference Engine**: `classifier.py` wraps a Keras/TensorFlow model for lightning-fast REST API predictions.
- **Fail-Safe Simulation Mode**: If TensorFlow crashes or the model file is missing during a live demo, the engine intelligently falls back to a mathematical simulation mode. **Your demo will never crash!**
- **Transfer Learning Pipeline**: `train_model.py` provides a complete training pipeline using MobileNetV2.
- **CLI Tester**: `test_model.py` allows you to test the AI on any local image without starting the FastAPI server.

## 1. How to Run the Inference (Test a Picture)
You can test the AI on any photo directly from the terminal. This is great for showing judges how fast the model is.
```powershell
# From the project root directory
python ai_engine/test_model.py path/to/your/image.jpg
```

## 2. Waste Classification Categories
The model is trained to recognize 4 specific classes:
1. **Hazardous**: Batteries, medical waste, chemicals. (Guidance: Specialized Disposal)
2. **Organic**: Food scraps, leaves, biodegradable waste. (Guidance: Composting)
3. **Recyclable**: Clean plastic, glass, cardboard. (Guidance: Recycling Facility)
4. **Non-Recyclable**: Wrappers, dirty plastics, mixed waste. (Guidance: Landfill)

## 3. How to Train Your Own Model (Optional)
If you want to train the model yourself (to show the judges you built the AI from scratch), follow these steps:

1. Create a folder named `dataset` inside the `ai_engine` folder.
2. Inside `dataset`, create 4 folders exactly named: `Hazardous`, `Non-Recyclable`, `Organic`, `Recyclable`.
3. Put at least 50-100 images of each waste type into their respective folders.
4. Run the training script:
```powershell
python ai_engine/train_model.py
```
This will train a highly accurate MobileNetV2 model and automatically save it to `models/waste_model.h5`.

## 4. API Integration
The FastAPI backend (`backend_api/main.py`) automatically imports this module. When the ESP32-CAM sends a POST request to `/predict`, the image is routed to `classifier.predict()`, and the JSON response is sent back with the detected class, confidence score, and disposal guidance.
