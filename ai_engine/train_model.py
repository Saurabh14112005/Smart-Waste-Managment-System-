import os
import argparse
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s - TRAIN - %(levelname)s - %(message)s")
logger = logging.getLogger("Trainer")

# Suppress TF warnings
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"

try:
    import tensorflow as tf
    from tensorflow.keras.preprocessing.image import ImageDataGenerator
    from tensorflow.keras.applications import MobileNetV2
    from tensorflow.keras.layers import Dense, GlobalAveragePooling2D, Dropout
    from tensorflow.keras.models import Model
    from tensorflow.keras.optimizers import Adam
    from tensorflow.keras.callbacks import ModelCheckpoint, EarlyStopping
except ImportError:
    logger.error("TensorFlow is not installed. Run: pip install tensorflow")
    exit(1)

# Configuration
IMAGE_SIZE = (224, 224)
BATCH_SIZE = 32
EPOCHS = 10
CLASSES = ["Hazardous", "Non-Recyclable", "Organic", "Recyclable"]
NUM_CLASSES = len(CLASSES)

def build_model():
    """Builds a MobileNetV2 based model for Transfer Learning."""
    logger.info("Building MobileNetV2 Base Model...")
    base_model = MobileNetV2(weights='imagenet', include_top=False, input_shape=(*IMAGE_SIZE, 3))
    
    # Freeze the base model
    base_model.trainable = False

    # Add custom classification head
    x = base_model.output
    x = GlobalAveragePooling2D()(x)
    x = Dropout(0.2)(x)
    x = Dense(128, activation='relu')(x)
    predictions = Dense(NUM_CLASSES, activation='softmax')(x)

    model = Model(inputs=base_model.input, outputs=predictions)
    
    model.compile(
        optimizer=Adam(learning_rate=0.001),
        loss='categorical_crossentropy',
        metrics=['accuracy']
    )
    return model

def main(dataset_path: str, model_save_path: str):
    if not os.path.exists(dataset_path):
        logger.error(f"Dataset path '{dataset_path}' not found!")
        logger.info("Please create a 'dataset' folder with subfolders for each class: " + ", ".join(CLASSES))
        return

    logger.info(f"Loading dataset from: {dataset_path}")
    
    # Data Augmentation for Training
    train_datagen = ImageDataGenerator(
        rescale=1./255,
        rotation_range=20,
        width_shift_range=0.2,
        height_shift_range=0.2,
        shear_range=0.2,
        zoom_range=0.2,
        horizontal_flip=True,
        validation_split=0.2 # Use 20% of data for validation
    )

    train_generator = train_datagen.flow_from_directory(
        dataset_path,
        target_size=IMAGE_SIZE,
        batch_size=BATCH_SIZE,
        class_mode='categorical',
        subset='training'
    )

    val_generator = train_datagen.flow_from_directory(
        dataset_path,
        target_size=IMAGE_SIZE,
        batch_size=BATCH_SIZE,
        class_mode='categorical',
        subset='validation'
    )

    # Ensure classes match our expected ordering
    logger.info(f"Class Indices: {train_generator.class_indices}")

    model = build_model()
    
    # Callbacks
    os.makedirs(os.path.dirname(model_save_path), exist_ok=True)
    checkpoint = ModelCheckpoint(
        model_save_path, 
        monitor='val_accuracy', 
        save_best_only=True, 
        mode='max', 
        verbose=1
    )
    early_stop = EarlyStopping(monitor='val_loss', patience=3, restore_best_weights=True)

    logger.info("Starting Training...")
    history = model.fit(
        train_generator,
        validation_data=val_generator,
        epochs=EPOCHS,
        callbacks=[checkpoint, early_stop]
    )
    
    logger.info(f"Training Complete! Best model saved to {model_save_path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Train Waste Classification Model")
    parser.add_argument("--dataset", type=str, default="dataset", help="Path to the dataset folder")
    parser.add_argument("--save", type=str, default="models/waste_model.h5", help="Path to save the trained model")
    args = parser.parse_args()
    
    main(args.dataset, args.save)
