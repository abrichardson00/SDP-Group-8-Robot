from flask import Flask
from flask_restx import Resource, Api, reqparse, inputs
from controller import Robot
from threading import Thread
from time import sleep
from functools import partial
from sys import stdout
from enum import Enum

app = Flask(__name__)
api = Api(app)

tray_regex_parser = reqparse.RequestParser()
# tray_regex_parser.add_argument("tray", type=inputs.regex("(B|F)(L|R)[0-4]"), required=True, strict=True)

CONTROL_STEP = 64

MAX_HEIGHT = 0.65
FB_MAX_EXTENT = 0.22
HEIGHT_MOD = 0.13
SHELF_TOP_CLEARANCE = 0.50
#these values were hard-coded and used repeatedly in the script. 
#Whilst it's fine for some of them, this is bad practice. -Blair

class State(Enum):
    IDLE = 1
    MOVING_TO_TRAY = 2
    EXTENDING_GRABBER = 3
    PICKING_UP_TRAY = 4
    RETRACTING_GRABBER = 5
    MOVING_TO_TOP = 6

"""

Retreiving:
- IDLE
- MOVING_UNDER_SHELF
- EXTENDING_ARM
- PICKING_UP_TRAY
- RETRACTING_ARM
- RETURNING_TO_TOP

Storing:
- IDLE
- MOVING_TO_SHELF
- EXTENDING_ARM(S)
- SETTING_DOWN_TRAY
- RETRACTING_ARMS
- RETURNING_TO_TOP

"""

system_state = State.IDLE
vertical_target = -1
horizontal_target = -1
left_grabber_target = -1
right_grabber_target = -1

@api.route("/retrieve/<string:tray>")
class Retrieve(Resource):
    def get(self, tray):

        global system_state

        if system_state != State.IDLE:
            return {"nope": tray}
        
        system_state = State.MOVING_TO_TRAY

        if tray[1] == "L":
            global left_grabber_target
            left_grabber_target = 1
        elif tray[1] == "R":
            global right_grabber_target
            right_grabber_target = 1

        global vertical_target
        vertical_target = 0.01 + int(tray[2])*HEIGHT_MOD

        global horizontal_target
        horizontal_target = (0.0 if tray[0] == "B" else -0.21)

        return {"yay": tray}


@api.route("/updown/<string:value>")
class UpDownResource(Resource):
    def get(self, value):
        # print("parsed %s" % float(value))
        global target_height
        target_height = float(value)
        return {"hello": "world"}

@api.route("/grabber/<string:value>")
class GrabberResource(Resource):
    def get(self, value):
        # print("parsed %s" % float(value))
        global right_grabber_target
        right_grabber_target = float(value)
        return {"hello": "world"}

def in_range(position, target):
    return target - 0.0001 < position < target + 0.0001

if __name__ == "__main__":

    theostore = Robot()
    
    vertical_motor = theostore.getDevice("vertical motor")
    
    vertical_motor_pos_sensor = theostore.getDevice("VertPos")
    vertical_motor_pos_sensor.enable(CONTROL_STEP)
    
    horizontal_motor = theostore.getDevice("horizontal motor")

    horizontal_motor_pos_sensor = theostore.getDevice("HoriPos")
    horizontal_motor_pos_sensor.enable(CONTROL_STEP)

    left_grabber_motor = theostore.getDevice("left grabber motor")
    
    left_grabber_motor_pos_sensor = theostore.getDevice("left_grabber_sensor")
    left_grabber_motor_pos_sensor.enable(CONTROL_STEP)

    right_grabber_motor = theostore.getDevice("right grabber motor")

    right_grabber_motor_pos_sensor = theostore.getDevice("grabberPosSensor")
    right_grabber_motor_pos_sensor.enable(CONTROL_STEP)

    print("Giving Flask a second to boot up...")

    theostore.step(CONTROL_STEP)

    # reloader is turned off because it breaks threading
    # setting daemon=True means that the webserver is terminated when the main thread exits
    api_thread = Thread(target=app.run, kwargs={"debug": True, "use_reloader": False, "threaded": True}, daemon=True)
    api_thread.start()
    
    for i in range(100):
        sleep(0.01)

    while theostore.step(CONTROL_STEP) != -1:

        if system_state == State.MOVING_TO_TRAY:
            vertical_motor.setPosition(vertical_target)
            current_vertical_pos = vertical_motor_pos_sensor.getValue()

            # once the platform has cleared the hole in the top
            if current_vertical_pos < SHELF_TOP_CLEARANCE:
                    horizontal_motor.setPosition(horizontal_target)
            current_horizontal_pos = horizontal_motor_pos_sensor.getValue()

            if in_range(current_vertical_pos, vertical_target) and in_range(current_horizontal_pos, horizontal_target):
                system_state = State.EXTENDING_GRABBER
        
        elif system_state == State.EXTENDING_GRABBER:
            if left_grabber_target != -1:
                left_grabber_motor.setPosition(FB_MAX_EXTENT)
                current_pos = left_grabber_motor_pos_sensor.getValue()
                if in_range(current_pos, FB_MAX_EXTENT):
                    system_state = State.PICKING_UP_TRAY
            elif right_grabber_target != -1:
                right_grabber_motor.setPosition(-FB_MAX_EXTENT)
                current_pos = right_grabber_motor_pos_sensor.getValue()
                if in_range(current_pos, -FB_MAX_EXTENT):
                    system_state = State.PICKING_UP_TRAY

        elif system_state == State.PICKING_UP_TRAY:
            vertical_motor.setPosition(vertical_target + 0.01)
            current_pos = vertical_motor_pos_sensor.getValue()
            if in_range(current_pos, vertical_target + 0.01):
                system_state = State.RETRACTING_GRABBER
        
        elif system_state == State.RETRACTING_GRABBER:
            if left_grabber_target != -1:
                left_grabber_motor.setPosition(0.0)
                current_pos = left_grabber_motor_pos_sensor.getValue()
                if in_range(current_pos, 0.0):
                    system_state = State.MOVING_TO_TOP
            elif right_grabber_target != -1:
                right_grabber_motor.setPosition(0.0)
                current_pos = right_grabber_motor_pos_sensor.getValue()
                if in_range(current_pos, 0.0):
                    system_state = State.MOVING_TO_TOP
        
        elif system_state == State.MOVING_TO_TOP:
            vertical_motor.setPosition(MAX_HEIGHT)
            horizontal_motor.setPosition(0.0)
            current_vertical_pos = vertical_motor_pos_sensor.getValue()
            current_horizontal_pos = horizontal_motor_pos_sensor.getValue()

            if not in_range(current_horizontal_pos, 0) and current_vertical_pos > SHELF_TOP_CLEARANCE:
                vertical_motor.setVelocity(0)
            else:
                vertical_motor.setVelocity(0.05)

            if in_range(current_vertical_pos, MAX_HEIGHT):
                system_state = State.IDLE
                vertical_target = -1
                horizontal_target = -1
                left_grabber_target = -1
                right_grabber_target = -1
