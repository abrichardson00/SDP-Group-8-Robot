import socket
import sys
import re
import collections
import subprocess
from datetime import datetime
from controller import Robot





## HELPER CLASSES ##############################################################

class Motor:
    """Helper for grouping motors with their position sensors."""
    def __init__(self, motor, sensor):
        self.motor = motor
        self.sensor = sensor
    
    def enable(self):
        self.sensor.enable(CONTROL_STEP)
    
    def get_position(self):
        return self.sensor.getValue()
    
    def set_position(self, target):
        self.motor.setPosition(target)
        
    def getMaxPosition(self):
        return self.motor.getMaxPosition()
        
    def getMinPosition(self):
        return self.motor.getMinPosition()


class Queue(collections.deque):
    """Wrapper for collections.deque with nicer method names."""
    def __init__(self, *args):
        super().__init__(self, *args)
    
    def enqueue(self, iter):
        self.extend(iter)
    
    def dequeue(self):
        return self.popleft()
    
    def peek(self):
        return self[0]
    
    def empty(self):
        return len(self) == 0


## INIT WEBOTS DEVICES #########################################################

theostore = Robot()

v_motor = Motor(
    theostore.getDevice("vertical motor"), 
    theostore.getDevice("VertPos"))

h_motor = Motor(
    theostore.getDevice("horizontal motor"),
    theostore.getDevice("HoriPos"))

lgrab_motor = Motor(
    theostore.getDevice("left grabber motor"),
    theostore.getDevice("left_grabber_sensor"))

rgrab_motor = Motor(
    theostore.getDevice("right grabber motor"),
    theostore.getDevice("grabberPosSensor"))

camera = theostore.getDevice("camera")

weightSense = theostore.getDevice("Weight Sensor")


## WEBOTS CONSTANTS ############################################################

# This is in ms and must be a multiple of the simulation timestep
CONTROL_STEP = 64 
CAMERA_SAMPLE_RATE = 512

# TODO: use v_motor.getMaxPosition instead
MAX_VERTICAL = v_motor.getMaxPosition()
MIN_VERTICAL = v_motor.getMinPosition() #bit weird because of nudge + offset

# Platform lines up with bottom shelf at this height
BOTTOM_SHELF = 0.0228  

# 13cm gap between each shelf
SHELF_SPACING = 0.130  

# Distance the platform lowers by to reach under each tray
BELOW_TRAY_OFFSET = -0.0130

# Used to slightly offset the platform and the shelf
# Increase the platform height by this when inserting
# Decrease the platform height by this when removing
NUDGE = 0.001

MAX_HORIZONTAL = h_motor.getMinPosition() #just how the orientation is.
MIN_HORIZONTAL = h_motor.getMaxPosition()

MIN_GRABBER = lgrab_motor.getMinPosition()
MAX_GRABBER = lgrab_motor.getMaxPosition() 

# Height at which the platform can safely move horizontally
SHELF_ROOF_CLEARANCE = 0.50


v_motor.enable()
h_motor.enable()
lgrab_motor.enable()
rgrab_motor.enable()
camera.enable(CAMERA_SAMPLE_RATE)
weightSense.enable(CAMERA_SAMPLE_RATE)

## INSTRUCTION QUEUE FUNCTIONS #################################################

"""
Instructions are stored as dictionaries.
Each dictionary entry has a Motor as a key and target pos as a value.
For example:

    instuction = {v_motor: 0.30, h_motor: 0.00}

Instructions are queued up and then dequeued when the simulation has followed
them (when each Motor's position sensor value matches its target position in
the instruction).

"""

def in_range(position, target):
    """Checks whether two numbers are very close."""
    return target - 0.0001 < position < target + 0.0001


def move_to_tray(level, depth, offset):
    """Returns instructions on how to move to a specified tray.
    
    level  -- the level (height) of the tray [0-4]
    depth  -- whether the tray is in the front or back (F|B)
    offset -- any additional height offset
    """
    instruction = {
        v_motor: BOTTOM_SHELF + (level * SHELF_SPACING) + offset,
        h_motor: MAX_HORIZONTAL if depth == "F" else MIN_HORIZONTAL
    }
    return instruction


def move_grabbers(left, right):
    """Returns instructions on how to extend grabbers.

    left  -- moves the left grabber (1=left, -1=right)
    right -- moves the right grabber (1=right, -1=left)
    """
    instruction = {
        lgrab_motor: left * MAX_GRABBER,
        rgrab_motor: right * -MAX_GRABBER
    }
    return instruction


def retrieve(depth, side, level):
    """Returns instructions on how to retrieve a tray from a shelf.

    depth -- whether the tray is in the front or back (F|B)
    side  -- whether the tray is in the left or right shelf (L|R)
    level -- the level (height) of the tray [0-4]
    """
    move_below_tray = move_to_tray(level, depth, BELOW_TRAY_OFFSET)

    if side == "L":
        extend_grabber = move_grabbers(1, 0)
    elif side == "R":
        extend_grabber = move_grabbers(0, 1)

    pick_up_tray = move_to_tray(level, depth, -NUDGE)

    instructions = [
        move_below_roof,
        move_below_tray,
        extend_grabber,
        pick_up_tray,
        retract_grabbers,
        move_below_roof,
        ascend_to_roof
    ]
    return instructions


def store(depth, side, level):
    """Returns instructions on how to store a tray on a shelf.

    depth -- whether the tray is in the front or back (F|B)
    side  -- whether the tray is in the left or right shelf (L|R)
    level -- the level (height) of the tray [0-4]
    """
    move_to_shelf = move_to_tray(level, depth, +NUDGE)

    if side == "L":
        extend_grabbers = move_grabbers(1, -1)
    elif side == "R":
        extend_grabbers = move_grabbers(-1, 1)
    
    release_tray = move_to_tray(level, depth, BELOW_TRAY_OFFSET)

    instructions = [
        move_below_roof,
        move_to_shelf,
        extend_grabbers,
        release_tray,
        retract_grabbers,
        move_below_roof,
        ascend_to_roof
    ]
    return instructions

# Steps used in both retrieval AND storage of trays
move_below_roof = {v_motor: SHELF_ROOF_CLEARANCE, h_motor: MIN_HORIZONTAL}
ascend_to_roof = {v_motor: MAX_VERTICAL}
retract_grabbers = move_grabbers(0, 0)


## MAIN PROGRAM ################################################################

def main_webots_loop():
    queue = Queue()

    while theostore.step(CONTROL_STEP) != -1:
        print(weightSense.getValue())
        # Try to read from connection
        # Throws a BlockingIOError if there is nothing to read
        try:
            received_message = connection.recv(32).decode("utf-8")
            received_message = received_message.upper()
        except BlockingIOError:
            received_message = ""

        # Try to match message with regular expression
        match = re.fullmatch(
            "(GET|PUT) ((F|B)(L|R)([0-4]))", 
            received_message)

        if match:
            print("Received '%s'." % received_message)

            # match.group returns the bracketed terms in the regex
            m = match.group
            command, name = m(1), m(2)
            depth, side, level = m(3), m(4), int(m(5))

            # Enqueue the appropriate instructions to the queue
            if command == "GET":
                instructions = retrieve(depth, side, level)
                connection.send(bytes("ACK", "utf-8"))
            
            elif command == "PUT":
                instructions = store(depth, side, level)
                
                if(queue.empty()):
                    filename = name + ".jpg"
                    camera.saveImage("images/" + filename, 90)
                    connection.send(bytes(filename, "utf-8"))
                else:
                    connection.send(bytes("ACK", "utf-8"))
                #this should solve the problem of the system taking arbitary photos when things are queued.
            
            queue.enqueue(instructions)
        elif received_message != "":
            print("Invalid command '%s'." % received_message)
            connection.send(bytes("BAD", "utf-8"))
        
        # If we haven't exhausted the instruction queue
        if not queue.empty():
            # Get current instruction but don't dequeue it yet
            curr_instruction = queue.peek()
            
            # For every motor: target pair in the current instruction
            target_positions_met = True
            for motor, target in curr_instruction.items():
                if not in_range(motor.get_position(), target):
                    target_positions_met = False
                    motor.set_position(target)
            
            # If we have fulfilled the current instruction, dequeue it
            if target_positions_met:
                queue.dequeue()

# The socket that we listen for commands on
server_socket = socket.create_server(("127.0.0.1", 5000))
server_socket.listen()

print("Waiting for a connection...")
theostore.step(CONTROL_STEP)  # Needed to display text

# This will block until we establish a connection
connection, address = server_socket.accept()

# Disable blocking for the incoming connection so Webots doesn't hang while we
# wait for commands to arrive
connection.setblocking(False)

print("Established connection!")
print("Starting webserver and simulation...")
theostore.step(CONTROL_STEP)

command = [sys.executable, "-m", "http.server", "80", "-d", "images/"]
image_server = subprocess.Popen(command)

# Start main loop...
try:
    main_webots_loop()
except KeyboardInterrupt:
    print("Exiting...")
finally:
    # Executes whether or not an exception was caught
    server_socket.close()
    image_server.kill()
