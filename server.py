import threading
import time
import grpc
import base64
import requests
import cv2
import os
from gtts import gTTS

# Import main from image_handling.py
from get_surroundings import main as get_surroundings

# Import SpotController class from spot_controller.py
from spot_controller import SpotController

def microphone_input_task():
    while True:
        # Code to handle microphone input
        # If movement is requested, check current surroundings and make API calls to Whisper API

        # Get description of surroundings
        surroundings = get_surroundings()


        pass

def terra_api_task():
    while True:
        # Code to call Terra API every second to check user health data
        time.sleep(1)

def spot_api_task():
    while True:
        # Code to handle incoming API calls requesting movement
        # Perform appropriate action via gRPC to the Spot API
        pass

# Define and start threads for each task

mic_thread = threading.Thread(target=microphone_input_task)
terra_thread = threading.Thread(target=terra_api_task)
spot_thread = threading.Thread(target=spot_api_task)

mic_thread.start()
terra_thread.start()
spot_thread.start()

# Keep the main thread running forever
while True:
    time.sleep(1)  # or any other necessary operation to keep the main thread alive
