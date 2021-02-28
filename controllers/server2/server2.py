from flask import Flask
from flask_restx import Resource, Api, reqparse, inputs
from controller import Robot
from threading import Thread
from time import sleep
from functools import partial
from sys import stdout

app = Flask(__name__)
api = Api(app)

tray_regex_parser = reqparse.RequestParser()
# tray_regex_parser.add_argument("tray", type=inputs.regex("(B|F)(L|R)[0-4]"), required=True, strict=True)

CONTROL_STEP = 64
target_height = -1
target_grabber = -1

@api.route("/retrieve/<string:tray>")
class Retrieve(Resource):
    def put(self, tray):
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

if __name__ == "__main__":

    theostore = Robot()
    vertical_motor = theostore.getDevice("vertical motor")
    vertical_motor_pos_sensor = theostore.getDevice("VertPos")
    vertical_motor_pos_sensor.enable(CONTROL_STEP)
    left_grabber_motor = theostore.getDevice("left grabber motor")

    print("Giving Flask a second to boot up...")

    theostore.step(CONTROL_STEP)

    # reloader is turned off because it breaks threading
    # setting daemon=True means that the webserver is terminated when the main thread exits
    api_thread = Thread(target=app.run, kwargs={"debug": True, "use_reloader": False, "threaded": True}, daemon=True)
    api_thread.start()
    
    for i in range(100):
        sleep(0.01)

    while theostore.step(CONTROL_STEP) != -1:
        # print("webots target pos = %s" % target_pos)
        if target_height != -1:
            print(vertical_motor_pos_sensor.getValue())
            # print("trying to move")
            # vertical_motor.setPosition(target_pos)
            vertical_motor.setPosition(target_height)
        if target_grabber != -1:
            left_grabber_motor.setPosition(target_grabber)

    