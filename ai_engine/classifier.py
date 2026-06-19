import os
import time
import logging
import numpy as np
from PIL import Image

logging.basicConfig(level=logging.INFO, format="%(asctime)s - AI-ENGINE - %(levelname)s - %(message)s")
logger = logging.getLogger("Classifier")

os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"
try:
    import tensorflow as tf
except ImportError as e:
    tf = None  # type: ignore[misc, assignment]
    logger.warning(
        "TensorFlow failed to import (%s). Place `waste_model.h5` under ai_engine/models/ "
        "and install MSVC++ x64 redistributable for GPU/CPU inference.",
        e,
    )

MODEL_PATH = os.path.join(os.path.dirname(__file__), "models", "waste_model.h5")


class WasteClassifier:
    """Waste-type classifier using only a trained Keras model file (no synthetic ML)."""

    def __init__(self):
        self.classes = ["Hazardous", "Non-Recyclable", "Organic", "Recyclable"]
        self.guidance = {
            "Organic": "Composting (Green Bin)",
            "Recyclable": "Recycling Facility (Blue Bin)",
            "Hazardous": "Specialized Disposal (Contact Local Unit)",
            "Non-Recyclable": "Landfill Processing (Red Bin)",
            "Uncertain": "Manual Verification Required",
        }
        self._backend = "none"
        self.model = None
        self._init_model()

    @property
    def active_backend(self) -> str:
        return self._backend

    def _init_model(self) -> None:
        if tf is None or not os.path.exists(MODEL_PATH):
            self.model = None
            self._backend = "none"
            if not os.path.exists(MODEL_PATH):
                logger.warning("No model at %s — vision API returns offline until you add weights.", MODEL_PATH)
            return
        try:
            logger.info("Loading Keras model from %s", MODEL_PATH)
            
            class LegacyBatchNormalization(tf.keras.layers.BatchNormalization):
                def __init__(self, **kwargs):
                    kwargs.pop('renorm', None)
                    kwargs.pop('renorm_clipping', None)
                    kwargs.pop('renorm_momentum', None)
                    super().__init__(**kwargs)
            
            model = tf.keras.models.load_model(
                MODEL_PATH, 
                custom_objects={'BatchNormalization': LegacyBatchNormalization}, 
                compile=False
            )
            device = "GPU" if tf.config.list_physical_devices("GPU") else "CPU"
            logger.info("AI engine on %s", device)
            model.predict(np.zeros((1, 224, 224, 3)), verbose=0)
            self.model = model
            self._backend = "keras"
        except Exception as e:
            logger.error("Keras load failed: %s", e)
            self.model = None
            self._backend = "none"

    def predict(self, img_input):
        if self._backend != "keras" or self.model is None:
            return "Engine Offline", 0.0, "Add ai_engine/models/waste_model.h5 and working TensorFlow", 0
        start = time.time()
        try:
            if isinstance(img_input, Image.Image):
                img = img_input.resize((224, 224))
            else:
                img = Image.fromarray(img_input).resize((224, 224))
            img_array = np.expand_dims(np.array(img) / 255.0, axis=0)
            preds = self.model.predict(img_array, verbose=0)
            class_idx = int(np.argmax(preds))
            confidence = float(np.max(preds))
            label = "Uncertain" if confidence < 0.60 else self.classes[class_idx]
            ms = int((time.time() - start) * 1000)
            return label, confidence, self.guidance.get(label), ms
        except Exception as e:
            logger.error("Inference: %s", e)
            return "Detection Error", 0.0, "Check image format", 0


classifier = WasteClassifier()
