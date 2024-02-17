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

ROBOT_IP = "10.0.0.3"#os.environ['ROBOT_IP']
SPOT_USERNAME = "admin"#os.environ['SPOT_USERNAME']
SPOT_PASSWORD = "2zqa8dgw7lor"#os.environ['SPOT_PASSWORD']

def start_spot_controller():
    # Use wrapper in context manager to lease control, turn on E-Stop, power on the robot and stand up at start
    # and to return lease + sit down at the end
    with SpotController(username=SPOT_USERNAME, password=SPOT_PASSWORD, robot_ip=ROBOT_IP) as spot:
        time.sleep(2)

        # Power on the robot and stand up
        spot.power_on_stand_up()

        # Move head to specified positions with intermediate time.sleep
        spot.move_head_in_points(yaws=[0.2, 0],
                                 pitches=[0.3, 0],
                                 rolls=[0.4, 0],
                                 sleep_after_point_reached=1)
        time.sleep(3)

        # Make Spot to move by goal_x meters forward and goal_y meters left
        # spot.move_to_goal(goal_x=0.5, goal_y=0)
        # time.sleep(3)

        # Control Spot by velocity in m/s (or in rad/s for rotation)
        spot.move_by_velocity_control(v_x=-0.3, v_y=0, v_rot=0, cmd_duration=2)
        time.sleep(3)

        # Make Spot to stand at specified height
        spot.stand_at_height(body_height=0.8)
        time.sleep(3)

        # Make Spot to bow with specified pitch and body height
        spot.bow(pitch=0.3, body_height=0.5, sleep_after_point_reached=1)
        time.sleep(3)

        # Make Spot to dust off with specified head positions
        spot.dust_off(yaws=[0.2, 0],
                        pitches=[0.3, 0],
                        rolls=[0.4, 0])
        time.sleep(3)

        # Make Spot to make stance with specified x and y offsets
        spot.make_stance(x_offset=0.5, y_offset=0.5)
        time.sleep(3)


        # Power off the robot and sit down
        # spot.power_off_sit_down()

        # Return spot as a result of the function
        return spot


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


# Start the Spot Controller
spot = start_spot_controller()

# Define and start threads for each task

# mic_thread = threading.Thread(target=microphone_input_task)
# terra_thread = threading.Thread(target=terra_api_task)
# spot_thread = threading.Thread(target=spot_api_task)

# mic_thread.start()
# terra_thread.start()
# spot_thread.start()

# Keep the main thread running forever
# while True:
#     time.sleep(1)  # or any other necessary operation to keep the main thread alive
