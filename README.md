# Face Recognition Model Training

This project trains a face recognition model using the Labeled Faces in the Wild (LFW) dataset. The model is built using TensorFlow and Keras.

## Dataset

The LFW dataset contains face images of people collected from the web. The script uses the deep-funneled version of the dataset for improved face alignment.

## Requirements

It's recommended to use a virtual environment:

```bash
# Create a virtual environment
python -m venv venv

# Activate the virtual environment
# On Linux/Mac:
source venv/bin/activate
# On Windows:
# venv\Scripts\activate

# Install the required packages
pip install -r requirements.txt
```

## Training the Model

The script `train_face_model.py` trains a face recognition model on 500 random images from the LFW dataset. To run the training:

```bash
python train_face_model.py
```

If you're running on a machine without a GPU, training might take some time. You can reduce the `epochs` parameter in the script for faster training.

## Model Architecture

The model uses a simple CNN architecture with the following layers:
- Three convolutional layers with max pooling
- Flatten layer
- Dense layer with dropout for regularization
- Output layer with softmax activation

## Results

After training, the script will:
1. Save the trained model to a directory named 'face_recognition_model'
2. Generate a plot of training and validation accuracy/loss as 'training_history.png'
3. Print the final validation accuracy

## Customization

You can modify the script to change:
- Number of training images (`num_samples` in `main()`)
- Image size (`img_size` in `main()`)
- Batch size and epochs
- Model architecture (in `build_face_model()`)

## Troubleshooting

If you encounter memory issues during training:
- Reduce the batch size
- Reduce the image size
- Use fewer training samples

For GPU-related issues:
- Make sure you have the correct version of CUDA and cuDNN installed for your TensorFlow version
- Try running with CPU only by setting: `os.environ["CUDA_VISIBLE_DEVICES"] = "-1"` 