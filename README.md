# AI Disaster Mapping Segmentation

A powerful AI-powered application for disaster mapping and image segmentation using Facebook's Segment Anything Model (SAM). This project provides both API endpoints and video processing capabilities for automated object detection and segmentation in disaster scenarios.

## 🚀 Features

- **Real-time Image Segmentation**: Process images using the state-of-the-art SAM model
- **Video Processing**: Batch process video frames for disaster mapping
- **REST API**: FastAPI-based endpoints for easy integration
- **Web Interface**: User-friendly interface for image upload and visualization
- **Multi-device Support**: Automatic GPU/CPU detection and utilization
- **Flexible Output**: Returns both processed images and segmentation metadata

## 📋 Requirements

- Python 3.8+
- CUDA-compatible GPU (optional, but recommended)
- 8GB+ RAM
- 2GB+ free disk space for model weights

## 🔧 Installation

Choose one of the following installation methods:

### Option 1: Docker (Recommended) 🐳

#### Prerequisites
- Docker and Docker Compose installed
- NVIDIA Docker runtime (for GPU support)

#### Quick Start with Docker

```bash
# Clone the repository
git clone https://github.com/Shellsight/disaster-mapping-segmentation.git
cd disaster-mapping-segmentation

# Build and run with Docker Compose
docker-compose up --build
```

The API will be available at `http://localhost:8080`

#### Manual Docker Commands

```bash
# Build the Docker image
docker build -t disaster-mapping-segmentation .

# Run the container (with GPU support)
docker run --gpus all -p 8080:8080 \
  -v $(pwd)/data:/app/data \
  -v $(pwd)/app/static:/app/app/static \
  disaster-mapping-segmentation

# Run without GPU (CPU only)
docker run -p 8080:8080 \
  -v $(pwd)/data:/app/data \
  -v $(pwd)/app/static:/app/app/static \
  disaster-mapping-segmentation
```

### Option 2: Local Installation

#### 1. Clone the Repository

```bash
git clone https://github.com/Shellsight/disaster-mapping-segmentation.git
cd disaster-mapping-segmentation
```

#### 2. Create Virtual Environment

```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

#### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

#### 4. Download SAM Model Weights

The application expects the SAM model weights to be placed in `app/models/`. Download the ViT-H SAM model:

```bash
mkdir -p app/models
cd app/models
wget https://dl.fbaipublicfiles.com/segment_anything/sam_vit_h_4b8939.pth
cd ../..
```

#### 5. Create Required Directories

```bash
mkdir -p app/static app/templates data
```

#### 6. Environment Configuration (Optional)

Create a `.env` file in the root directory for custom configuration:

```bash
# .env
APP_NAME="AI Disaster Mapping API"
DEBUG=True
MODEL_PATH="app/models/sam_vit_h_4b8939.pth"
MODEL_TYPE="vit_h"
```

## 🏃‍♂️ Quick Start

### With Docker (Recommended)

```bash
# Quick start with Docker Compose
docker-compose up --build

# Or build and run manually
docker build -t disaster-mapping-segmentation .
docker run --gpus all -p 8080:8080 disaster-mapping-segmentation
```

### Local Development

```bash
# Activate virtual environment
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Start the API server
uvicorn app.main:app --host 0.0.0.0 --port 8080 --reload
```

The API will be available at `http://localhost:8080`

### API Documentation

Once the server is running, access the interactive API documentation:
- Swagger UI: `http://localhost:8080/docs`
- ReDoc: `http://localhost:8080/redoc`

### Health Check

```bash
curl http://localhost:8080/health
```

## 📖 Usage

### 1. Image Segmentation via API

#### Using curl

```bash
curl -X POST "http://localhost:8080/segment" \
     -H "accept: application/json" \
     -H "Content-Type: multipart/form-data" \
     -F "image=@path/to/your/image.jpg"
```

#### Using Python requests

```python
import requests

url = "http://localhost:8080/segment"
files = {"image": open("path/to/your/image.jpg", "rb")}

response = requests.post(url, files=files)

if response.status_code == 200:
    # Save processed image
    with open("output.png", "wb") as f:
        f.write(response.content)
    
    # Get metadata from headers
    total_objects = response.headers.get('X-Total-Objects')
    processing_time = response.headers.get('X-Processing-Time')
    
    print(f"Found {total_objects} objects in {processing_time}s")
```

### 2. Video Processing

For batch processing of video files:

```bash
python run.py
```

This script will:
- Process frames from `demo.mp4`
- Send each frame to the segmentation API
- Generate an output video with segmented objects
- Save the result to `app/static/processed_video.mp4`

### 3. Web Interface

Navigate to `http://localhost:8080` in your browser to access the web interface for uploading and processing images.

## 🔍 API Reference

### POST /segment

Segments objects in an uploaded image using SAM.

**Request:**
- Method: `POST`
- Content-Type: `multipart/form-data`
- Body: Image file

**Response:**
- Content: Processed image with colored segmentation masks
- Headers:
  - `X-Total-Objects`: Number of detected objects
  - `X-Processing-Time`: Processing time in seconds
  - `X-Segmentation-Results`: JSON string with detailed results

**Example Response Headers:**
```
X-Total-Objects: 15
X-Processing-Time: 2.34
X-Segmentation-Results: {"detected_objects": [], "processing_time": 2.34, "total_objects": 15}
```

### GET /health

Health check endpoint.

**Response:**
```json
{
  "status": "ok",
  "message": "AI Disaster Mapping API is running 🚀"
}
```

## 🏗️ Project Structure

```
disaster-mapping-segmentation/
├── app/
│   ├── api/
│   │   └── segment.py          # API endpoints
│   ├── core/
│   │   ├── config.py           # Configuration settings
│   │   └── logger.py           # Logging configuration
│   ├── models/                 # SAM model weights
│   ├── services/
│   │   └── segment.py          # Core segmentation logic
│   ├── static/                 # Static files
│   ├── templates/              # HTML templates
│   └── main.py                 # FastAPI application
├── data/                       # Data directory
├── notebooks/                  # Jupyter notebooks
├── requirements.txt            # Python dependencies
├── run.py                      # Video processing script
└── README.md                   # This file
```

## ⚙️ Configuration

The application uses Pydantic settings for configuration. Key settings include:

- `MODEL_PATH`: Path to SAM model weights
- `MODEL_TYPE`: SAM model variant (`vit_h`, `vit_l`, `vit_b`)
- `DEVICE`: Computing device (`cuda` or `cpu`)
- `DEBUG`: Enable debug mode

## 🚀 Performance Tips

1. **GPU Acceleration**: Ensure CUDA is available for faster processing
2. **Model Selection**: Use `vit_h` for best quality, `vit_b` for faster processing
3. **Image Preprocessing**: Resize large images before processing
4. **Batch Processing**: Use the video processing script for multiple images

## 🛠️ Development

### Running Tests

```bash
pytest
```

### Code Formatting

```bash
black .
isort .
```

### Type Checking

```bash
mypy app/
```

## 🐳 Docker Details

### Docker Features

- **Multi-stage build**: Optimized for production deployment
- **CUDA support**: GPU acceleration for faster inference
- **Health checks**: Built-in container health monitoring
- **Volume mounts**: Persistent data and output storage
- **Environment configuration**: Easy customization via environment variables

### Docker Commands

```bash
# Build the image
docker build -t disaster-mapping-segmentation .

# Run with GPU support (requires nvidia-docker)
docker run --gpus all -p 8080:8080 \
  -v $(pwd)/data:/app/data \
  -v $(pwd)/app/static:/app/app/static \
  disaster-mapping-segmentation

# Run CPU-only
docker run -p 8080:8080 \
  -v $(pwd)/data:/app/data \
  -v $(pwd)/app/static:/app/app/static \
  disaster-mapping-segmentation

# View logs
docker logs disaster-mapping-segmentation

# Access container shell
docker exec -it disaster-mapping-segmentation /bin/bash
```

### Docker Compose Services

The `docker-compose.yml` includes:
- **API Service**: Main application with GPU support
- **Volume Mounts**: For data persistence and output access
- **Health Checks**: Automatic service monitoring
- **Restart Policy**: Automatic container restart on failure

### Environment Variables

Configure the Docker container using environment variables:

```bash
# docker-compose.yml or docker run -e
APP_NAME="AI Disaster Mapping API"
DEBUG=true
MODEL_PATH="app/models/sam_vit_h_4b8939.pth"
MODEL_TYPE="vit_h"
```

### GPU Requirements

For GPU acceleration:
1. Install [NVIDIA Docker runtime](https://github.com/NVIDIA/nvidia-docker)
2. Ensure CUDA-compatible GPU is available
3. Use `--gpus all` flag or Docker Compose GPU configuration

## 📊 Model Information

This project uses Facebook's Segment Anything Model (SAM):
- **Model**: ViT-H (Vision Transformer - Huge)
- **Parameters**: 630M
- **Input**: RGB images of any size
- **Output**: Instance segmentation masks

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- [Facebook Research](https://github.com/facebookresearch/segment-anything) for the Segment Anything Model
- [FastAPI](https://fastapi.tiangolo.com/) for the web framework
- [OpenCV](https://opencv.org/) for image processing capabilities

## 📞 Support

For issues and questions:
1. Check the [Issues](../../issues) page
2. Review the API documentation at `/docs`
3. Ensure all dependencies are correctly installed

---

**Note**: Make sure to download the SAM model weights before running the application. The model file is approximately 2.6GB and requires a stable internet connection for download.