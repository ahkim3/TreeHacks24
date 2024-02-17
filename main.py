# import base64
# import requests
# import cv2
# import os
# from gtts import gTTS
#
# # Play an audio sample using ffplay, with no display and auto exit on completion. This is useful for background audio feedback.
# audio_filename = "file_example_MP3_2MG.mp3"
# os.system(f"ffplay -nodisp -autoexit -loglevel quiet {audio_filename}")
#
# def capture_image():
#     # Utilize DirectShow with cv2.VideoCapture to ensure high-resolution image capture. This approach is beneficial for capturing detailed images.
#     cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
#
#     # Set the desired frame width and height for the captured image to ensure the image has sufficient resolution for processing.
#     cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
#     cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
#
#     # Attempt to capture a single frame. If successful, 'rv' is True and 'image' contains the captured frame.
#     rv, image = cap.read()
#
#     # Always release the camera immediately after capturing the image to free hardware resources.
#     cap.release()
#
#     if not rv:
#         # If the frame capture failed, inform the user and exit the program.
#         print("Failed to capture image.")
#         exit()
#
#     # Return the captured image frame for further processing.
#     return image
#
# def encode_image(image_path):
#     # Open the image file in binary mode, read its contents, and encode it to base64. This encoding is necessary for transmitting binary image data over JSON in the API request.
#     with open(image_path, "rb") as image_file:
#         return base64.b64encode(image_file.read()).decode('utf-8')
#
# # Capture an image from the camera and obtain the image data as a matrix.
# image = capture_image()
#
# # Save the captured image matrix to a jpg file, providing a visual confirmation of what was captured.
# image_filename = "captured_image.jpg"
# cv2.imwrite(image_filename, image)
# print(f"Image saved as {image_filename}")
# print(f"Image Dimensions: {image.shape}")  # Display the dimensions of the captured image for informational purposes.
#
# # Encode the saved image to base64 for transmission. This step is required to prepare the image data for inclusion in the JSON payload of the API request.
# base64_image = encode_image(image_filename)
#
# # Retrieve the OpenAI API Key from environment variables for secure API access. Using environment variables helps keep sensitive information out of the script.
# api_key = os.getenv("OPENAI_API_KEY")
# if not api_key:
#     # If the API key is not set, raise an error to prevent the script from proceeding without proper authentication.
#     raise ValueError("The OpenAI API key must be set as an environment variable 'OPENAI_API_KEY'.")
#
# # Configure the request headers, including the Content-Type and Authorization with the retrieved API key.
# headers = {
#     "Content-Type": "application/json",
#     "Authorization": f"Bearer {api_key}"
# }
#
# # Prepare the JSON payload with the base64 encoded image. The payload specifies the model to use and includes the encoded image data for analysis.
# payload = {
#     "model": "gpt-4-vision-preview",
#     "messages": [
#         {
#             "role": "user",
#             "content": [
#                 {
#                     "type": "text",
#                     "text": "What’s in this image?"
#                 },
#                 {
#                     "type": "image_url",
#                     "image_url": {
#                         "url": f"data:image/jpeg;base64,{base64_image}"  # The base64 image data is embedded directly in the payload.
#                     }
#                 }
#             ]
#         }
#     ],
#     "max_tokens": 1000  # Specifies the maximum length of the response to ensure detailed analysis without exceeding API limits.
# }
#
# # Send the prepared request to the OpenAI vision API and capture the response for analysis.
# response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload)
#
# # Print the API response to the console. This response contains the AI's interpretation of the image content.
# print(response.json())
#
# # Check if the request was successful
# if response.status_code == 200:
#     response_data = response.json()
#     try:
#         text_to_read = response_data["choices"][0]["message"]["content"]
#         print(text_to_read)  # Print the text to console for verification
#
#         # Convert the extracted text to speech
#         tts = gTTS(text=text_to_read, lang='en', slow=False)
#         tts_file = "response_tts.mp3"
#         tts.save(tts_file)
#
#         # Play the generated speech file
#         os.system(f"ffplay -nodisp -autoexit -loglevel quiet {tts_file}")
#     except KeyError:
#         print("The expected data was not found in the response.")
# else:
#     print("Failed to get a valid response from OpenAI API.")
#

# Copyright (c) 2023 Boston Dynamics, Inc.  All rights reserved.
#
# Downloading, reproducing, distributing or otherwise using the SDK Software
# is subject to the terms and conditions of the Boston Dynamics Software
# Development Kit License (20191101-BDSDK-SL).

"""Tutorial to show how to walk the robot to an object, usually in preparation for manipulation.
"""
import argparse
import sys
import time

import cv2
import numpy as np
from google.protobuf import wrappers_pb2

import bosdyn.client
import bosdyn.client.estop
import bosdyn.client.lease
import bosdyn.client.util
from bosdyn.api import geometry_pb2, image_pb2, manipulation_api_pb2
from bosdyn.client.image import ImageClient
from bosdyn.client.manipulation_api_client import ManipulationApiClient
from bosdyn.client.robot_command import RobotCommandClient, blocking_stand

g_image_click = None
g_image_display = None


def walk_to_object(config):
    """Get an image and command the robot to walk up to a selected object.
       We'll walk "up to" the object, not on top of it.  The idea is that you
       want to interact or manipulate the object."""

    # See hello_spot.py for an explanation of these lines.
    bosdyn.client.util.setup_logging(config.verbose)

    sdk = bosdyn.client.create_standard_sdk('WalkToObjectClient')
    robot = sdk.create_robot(config.hostname)
    bosdyn.client.util.authenticate(robot)
    robot.time_sync.wait_for_sync()

    assert robot.has_arm(), 'Robot requires an arm to run this example.'

    # Verify the robot is not estopped and that an external application has registered and holds
    # an estop endpoint.
    assert not robot.is_estopped(), 'Robot is estopped. Please use an external E-Stop client, ' \
                                    'such as the estop SDK example, to configure E-Stop.'

    lease_client = robot.ensure_client(bosdyn.client.lease.LeaseClient.default_service_name)
    image_client = robot.ensure_client(ImageClient.default_service_name)
    manipulation_api_client = robot.ensure_client(ManipulationApiClient.default_service_name)

    with bosdyn.client.lease.LeaseKeepAlive(lease_client, must_acquire=True, return_at_exit=True):
        # Now, we are ready to power on the robot. This call will block until the power
        # is on. Commands would fail if this did not happen. We can also check that the robot is
        # powered at any point.
        robot.logger.info('Powering on robot... This may take a several seconds.')
        robot.power_on(timeout_sec=20)
        assert robot.is_powered_on(), 'Robot power on failed.'
        robot.logger.info('Robot powered on.')

        # Tell the robot to stand up. The command service is used to issue commands to a robot.
        # The set of valid commands for a robot depends on hardware configuration. See
        # RobotCommandBuilder for more detailed examples on command building. The robot
        # command service requires timesync between the robot and the client.
        robot.logger.info('Commanding robot to stand...')
        command_client = robot.ensure_client(RobotCommandClient.default_service_name)
        blocking_stand(command_client, timeout_sec=10)
        robot.logger.info('Robot standing.')

        # Take a picture with a camera
        robot.logger.info('Getting an image from: %s', config.image_source)
        image_responses = image_client.get_image_from_sources([config.image_source])

        if len(image_responses) != 1:
            print(f'Got invalid number of images: {len(image_responses)}')
            print(image_responses)
            assert False

        image = image_responses[0]
        if image.shot.image.pixel_format == image_pb2.Image.PIXEL_FORMAT_DEPTH_U16:
            dtype = np.uint16
        else:
            dtype = np.uint8
        img = np.fromstring(image.shot.image.data, dtype=dtype)
        if image.shot.image.format == image_pb2.Image.FORMAT_RAW:
            img = img.reshape(image.shot.image.rows, image.shot.image.cols)
        else:
            img = cv2.imdecode(img, -1)

        # # Show the image to the user and wait for them to click on a pixel
        # robot.logger.info('Click on an object to walk up to...')
        # image_title = 'Click to walk up to something'
        # cv2.namedWindow(image_title)
        # cv2.setMouseCallback(image_title, cv_mouse_callback)
        #
        # global g_image_click, g_image_display
        # g_image_display = img
        # cv2.imshow(image_title, g_image_display)
        # while g_image_click is None:
        #     key = cv2.waitKey(1) & 0xFF
        #     if key == ord('q') or key == ord('Q'):
        #         # Quit
        #         print('"q" pressed, exiting.')
        #         exit(0)

        g_image_click = (500, 500)

        robot.logger.info('Walking to object at image location (%s, %s)', g_image_click[0],
                          g_image_click[1])

        walk_vec = geometry_pb2.Vec2(x=g_image_click[0], y=g_image_click[1])

        # Optionally populate the offset distance parameter.
        if config.distance is None:
            offset_distance = None
        else:
            offset_distance = wrappers_pb2.FloatValue(value=config.distance)

        # Build the proto
        walk_to = manipulation_api_pb2.WalkToObjectInImage(
            pixel_xy=walk_vec, transforms_snapshot_for_camera=image.shot.transforms_snapshot,
            frame_name_image_sensor=image.shot.frame_name_image_sensor,
            camera_model=image.source.pinhole, offset_distance=offset_distance)

        # Ask the robot to pick up the object
        walk_to_request = manipulation_api_pb2.ManipulationApiRequest(
            walk_to_object_in_image=walk_to)

        # Send the request
        cmd_response = manipulation_api_client.manipulation_api_command(
            manipulation_api_request=walk_to_request)

        # Get feedback from the robot
        while True:
            time.sleep(0.25)
            feedback_request = manipulation_api_pb2.ManipulationApiFeedbackRequest(
                manipulation_cmd_id=cmd_response.manipulation_cmd_id)

            # Send the request
            response = manipulation_api_client.manipulation_api_feedback_command(
                manipulation_api_feedback_request=feedback_request)

            print('Current state: ',
                  manipulation_api_pb2.ManipulationFeedbackState.Name(response.current_state))

            if response.current_state == manipulation_api_pb2.MANIP_STATE_DONE:
                break

        robot.logger.info('Finished.')
        robot.logger.info('Sitting down and turning off.')

        # Power the robot off. By specifying "cut_immediately=False", a safe power off command
        # is issued to the robot. This will attempt to sit the robot before powering off.
        robot.power_off(cut_immediately=False, timeout_sec=20)
        assert not robot.is_powered_on(), 'Robot power off failed.'
        robot.logger.info('Robot safely powered off.')


def cv_mouse_callback(event, x, y, flags, param):
    global g_image_click, g_image_display
    clone = g_image_display.copy()
    if event == cv2.EVENT_LBUTTONUP:
        g_image_click = (x, y)
    else:
        # Draw some lines on the image.
        #print('mouse', x, y)
        color = (30, 30, 30)
        thickness = 2
        image_title = 'Click to walk up to something'
        height = clone.shape[0]
        width = clone.shape[1]
        cv2.line(clone, (0, y), (width, y), color, thickness)
        cv2.line(clone, (x, 0), (x, height), color, thickness)
        cv2.imshow(image_title, clone)


def arg_float(x):
    try:
        x = float(x)
    except ValueError:
        raise argparse.ArgumentTypeError(f'{repr(x)} not a number')
    return x


def main():
    """Command line interface."""
    parser = argparse.ArgumentParser()
    bosdyn.client.util.add_base_arguments(parser)
    parser.add_argument('-i', '--image-source', help='Get image from source',
                        default='frontleft_fisheye_image')
    parser.add_argument('-d', '--distance', help='Distance from object to walk to (meters).',
                        default=None, type=arg_float)
    options = parser.parse_args()

    try:
        walk_to_object(options)
        return True
    except Exception as exc:  # pylint: disable=broad-except
        logger = bosdyn.client.util.get_logger()
        logger.exception('Threw an exception')
        return False


if __name__ == '__main__':
    if not main():
        sys.exit(1)
