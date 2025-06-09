import requests
import os
import numpy as np
from PIL import Image
import cv2
import json

api_endpoint = "http://localhost:8080/segment"
video_path = "demo.mp4"

cap = cv2.VideoCapture(video_path)
fps = cap.get(cv2.CAP_PROP_FPS)
width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

# Save the processed video
output_path = "app/static/processed_video.mp4"
fourcc = cv2.VideoWriter_fourcc(*'mp4v')
out = cv2.VideoWriter(output_path, fourcc, fps, (640, 640))

frame_count = 0

while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        print("End of video or error reading frame.")
        break

    frame_count += 1
    if frame_count % 30 != 0:  # Process every 30th frame
        continue

    print(f"Processing frame {frame_count}...")
    frame = cv2.resize(frame, (640, 640))  # Ensure frame size matches output video
    # Convert frame to bytes
    _, buffer = cv2.imencode('.jpg', frame)
    frame_bytes = buffer.tobytes()

    try:
        # Send the frame to the API
        response = requests.post(api_endpoint, files={"image": frame_bytes}, timeout=30)
        
        print(f"Response status: {response.status_code}")
        print(f"Response headers: {response.headers}")
        print(f"Response content length: {len(response.content)}")
        
        if response.status_code == 200:
            # The response body contains the processed image as raw bytes
            # Segmentation results are in the headers
            try:
                # Get segmentation results from headers
                segmentation_results = response.headers.get('X-Segmentation-Results')
                processing_time = response.headers.get('X-Processing-Time')
                total_objects = response.headers.get('X-Total-Objects')
                
                if segmentation_results:
                    results = json.loads(segmentation_results)
                    print(f"Frame {frame_count}: Found {total_objects} objects in {processing_time}s")
                
                # Decode the processed image from response body
                processed_image = cv2.imdecode(np.frombuffer(response.content, np.uint8), cv2.IMREAD_COLOR)
                
                if processed_image is None:
                    print("Failed to decode processed image, using original frame")
                    processed_image = frame
                    
            except Exception as e:
                print(f"Error processing response: {e}")
                processed_image = frame

            out.write(processed_image)
            
        elif response.status_code == 500:
            print("Server error (500):")
            try:
                error_detail = response.json().get('detail', 'Unknown error')
                print(f"Error details: {error_detail}")
            except:
                print(f"Raw error response: {response.text}")
            
            # Use original frame as fallback
            processed_image = frame  
            out.write(processed_image)
            
        else:
            print(f"HTTP Error: {response.status_code}")
            print(f"Response: {response.text}")
            
            # Use original frame as fallback
            processed_image = frame
            out.write(processed_image)

    except requests.exceptions.RequestException as e:
        print(f"Request error: {e}")
        # Use original frame as fallback
        processed_image = frame
        cv2.imshow('Processed Frame', processed_image)
        out.write(processed_image)
    
    except Exception as e:
        print(f"Unexpected error: {e}")
        # Use original frame as fallback
        processed_image = frame
        out.write(processed_image)

print(f"Processed {frame_count} frames")
cap.release()
out.release()
print(f"Output video saved to: {output_path}")