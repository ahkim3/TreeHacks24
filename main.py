import base64
import requests
import cv2
import os
from gtts import gTTS

# Play an audio sample using ffplay, with no display and auto exit on completion. This is useful for background audio feedback.
audio_filename = "file_example_MP3_2MG.mp3"
os.system(f"ffplay -nodisp -autoexit -loglevel quiet {audio_filename}")

def capture_image():
    # Utilize DirectShow with cv2.VideoCapture to ensure high-resolution image capture. This approach is beneficial for capturing detailed images.
    cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)

    # Set the desired frame width and height for the captured image to ensure the image has sufficient resolution for processing.
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

    # Attempt to capture a single frame. If successful, 'rv' is True and 'image' contains the captured frame.
    rv, image = cap.read()

    # Always release the camera immediately after capturing the image to free hardware resources.
    cap.release()

    if not rv:
        # If the frame capture failed, inform the user and exit the program.
        print("Failed to capture image.")
        exit()

    # Return the captured image frame for further processing.
    return image 

def encode_image(image_path):
    # Open the image file in binary mode, read its contents, and encode it to base64. This encoding is necessary for transmitting binary image data over JSON in the API request.
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

# Capture an image from the camera and obtain the image data as a matrix.
image = capture_image()

# Save the captured image matrix to a jpg file, providing a visual confirmation of what was captured.
image_filename = "captured_image.jpg"
cv2.imwrite(image_filename, image)
print(f"Image saved as {image_filename}")
print(f"Image Dimensions: {image.shape}")  # Display the dimensions of the captured image for informational purposes.

# Encode the saved image to base64 for transmission. This step is required to prepare the image data for inclusion in the JSON payload of the API request.
base64_image = encode_image(image_filename)

# Retrieve the OpenAI API Key from environment variables for secure API access. Using environment variables helps keep sensitive information out of the script.
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    # If the API key is not set, raise an error to prevent the script from proceeding without proper authentication.
    raise ValueError("The OpenAI API key must be set as an environment variable 'OPENAI_API_KEY'.")

# Configure the request headers, including the Content-Type and Authorization with the retrieved API key.
headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {api_key}"
}

# Prepare the JSON payload with the base64 encoded image. The payload specifies the model to use and includes the encoded image data for analysis.
payload = {
    "model": "gpt-4-vision-preview",
    "messages": [
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": "What’s in this image?"
                },
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/jpeg;base64,{base64_image}"  # The base64 image data is embedded directly in the payload.
                    }
                }
            ]
        }
    ],
    "max_tokens": 1000  # Specifies the maximum length of the response to ensure detailed analysis without exceeding API limits.
}

# Send the prepared request to the OpenAI vision API and capture the response for analysis.
response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload)

# Print the API response to the console. This response contains the AI's interpretation of the image content.
print(response.json())

# Check if the request was successful
if response.status_code == 200:
    response_data = response.json()
    try:
        text_to_read = response_data["choices"][0]["message"]["content"]
        print(text_to_read)  # Print the text to console for verification
        
        # Convert the extracted text to speech
        tts = gTTS(text=text_to_read, lang='en', slow=False)
        tts_file = "response_tts.mp3"
        tts.save(tts_file)
        
        # Play the generated speech file
        os.system(f"ffplay -nodisp -autoexit -loglevel quiet {tts_file}")
    except KeyError:
        print("The expected data was not found in the response.")
else:
    print("Failed to get a valid response from OpenAI API.")

