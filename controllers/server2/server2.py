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
# target_height = -1
# target_grabber = -1

class State(Enum):
    IDLE = 1
    MOVING_TO_TRAY = 2
    EXTENDING_GRABBER = 3
    PICKING_UP_TRAY = 4
    RETRACTING_GRABBER = 5
    MOVING_TO_TOP = 6

system_state = State.IDLE
vertical_target = -1
horizontal_target = -1
left_grabber_target = -1

@api.route("/retrieve/<string:tray>")
class Retrieve(Resource):
    def get(self, tray):

        global system_state
        system_state = State.MOVING_TO_TRAY

        global vertical_target
        vertical_target = 0.01 + int(tray[2])*0.13

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
        global target_grabber
        target_grabber = float(value)
        return {"hello": "world"}

def in_range(position, target):
    return target - 0.0001 < position < target + 0.0001

if __name__ == "__main__":

    theostore = Robot()
    
    vertical_motor = theostore.getDevice("vertical motor")
    
    vertical_motor_pos_sensor = theostore.getDevice("VertPos")
    vertical_motor_pos_sensor.enable(CONTROL_STEP)
    
    left_grabber_motor = theostore.getDevice("left grabber motor")
    
    left_grabber_motor_pos_sensor = theostore.getDevice("left_grabber_sensor")
    left_grabber_motor_pos_sensor.enable(CONTROL_STEP)

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
            current_pos = vertical_motor_pos_sensor.getValue()
            if in_range(current_pos, vertical_target):
                system_state = State.EXTENDING_GRABBER
        
        elif system_state == State.EXTENDING_GRABBER:
            left_grabber_motor.setPosition(0.22)
            current_pos = left_grabber_motor_pos_sensor.getValue()
            if in_range(current_pos, 0.22):
                system_state = State.PICKING_UP_TRAY

        elif system_state == State.PICKING_UP_TRAY:
            vertical_motor.setPosition(vertical_target + 0.01)
            current_pos = vertical_motor_pos_sensor.getValue()
            if in_range(current_pos, vertical_target + 0.01):
                system_state = State.RETRACTING_GRABBER
        
        elif system_state == State.RETRACTING_GRABBER:
            left_grabber_motor.setPosition(0.0)
            current_pos = left_grabber_motor_pos_sensor.getValue()
            if in_range(current_pos, 0.0):
                system_state = State.MOVING_TO_TOP
        
        elif system_state == State.MOVING_TO_TOP:
            vertical_motor.setPosition(0.65)
            current_pos = vertical_motor_pos_sensor.getValue()
            if in_range(current_pos, 0.65):
                system_state = State.IDLE
        
        

            
    