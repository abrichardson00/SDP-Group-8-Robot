import socket
import sys
import re
import collections
import subprocess
import select
from pyzbar import pyzbar
from pyzbar.pyzbar import ZBarSymbol
from PIL import Image
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
    
    def enqueue(self, item):
        self.append(item)

    def enqueue_all(self, iter):
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
CAMERA_SAMPLE_RATE = 64

MAX_VERTICAL = v_motor.getMaxPosition()

# Platform lines up with bottom shelf at this height
BOTTOM_SHELF = 0.0228  

# 13cm gap between each shelf
SHELF_SPACING = 0.130  

# Distance the platform lowers by to reach under each tray
BELOW_TRAY_OFFSET = -0.0130

# Position that the platform moves to before taking a photo
TAKE_PHOTO_VERTICAL = 0.48

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
    return target - 0.005 < position < target + 0.005


def move_to_tray(level, depth, offset):
    """Returns instructions on how to move to a specified tray.
    
    level  -- the level (height) of the tray [0-4]
    depth  -- whether the tray is in the front or back (F|B)
    offset -- any additional height offset
    """
    instruction = {
        v_motor: BOTTOM_SHELF + (int(level) * SHELF_SPACING) + offset,
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
    move_to_shelf = move_to_tray(level, depth, +NUDGE*3)

    if side == "L":
        extend_grabbers = move_grabbers(1, -1)
    elif side == "R":
        extend_grabbers = move_grabbers(-1, 1)
    
    release_tray = move_to_tray(level, depth, BELOW_TRAY_OFFSET)

    instructions = [
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
move_to_camera_position = {v_motor: TAKE_PHOTO_VERTICAL}
retract_grabbers = move_grabbers(0, 0)


## IMAGE RECOGNITION ###########################################################


def tray_from_barcode(image):

    barcodes = pyzbar.decode(image, symbols=[ZBarSymbol.EAN8])
    
    # There are multiple barcodes on the tray for redundancy
    # If we find none, there is likely no tray
    # If we find more than one, just read the first one
    if not barcodes:
        return None

    data = barcodes[0].data.decode("utf-8")[4:7]
    if re.fullmatch("[01][01][0-4]", data):
        data = ("B" if data[0] == "0" else "F") + ("L" if data[1] == "0" else "R") + data[2]
        return data
    
    return None


## MAIN PROGRAM ################################################################


command = [sys.executable, "-m", "http.server", "80", "-d", "images/"]
image_server = subprocess.Popen(command)

print("Image server started")

print("Listening on socket")
server_socket = socket.create_server(("127.0.0.1", 5000), backlog=1)
server_socket.setblocking(False)
client_socket = None


def main_webots_loop():
    queue = Queue()

    global server_socket
    global client_socket

    while theostore.step(CONTROL_STEP) != -1:

        received_message = ""

        readable_sockets, _, _ = select.select(
            [server_socket] + ([client_socket] if client_socket else []), 
            [], 
            [], 
            0)

        for socket in readable_sockets:

            # If someone is trying to establish a connection
            if socket == server_socket:
                # If there isn't an active connection already
                if client_socket is None:
                    connection, address = server_socket.accept()
                    print("Accepted connection from client at " + address[0])
                    connection.setblocking(False)
                    client_socket = connection
            
            else:
                msg = socket.recv(32).decode("utf-8").upper()
                if msg:
                    received_message = msg
                else:
                    socket.close()
                    client_socket = None
                    print("Connection closed")


        # Don't parse any commands while we are busy moving trays around
        if received_message and queue.empty():

            get_command_match = re.fullmatch("GET ([FB][LR][0-4])", received_message)
            if get_command_match:
                # match.group(1) returns the bracketed term in the regex
                # match.group(0) would return the entire string
                tray_code = get_command_match.group(1)
                
                # Enqueue the appropriate instructions to the queue
                instructions = retrieve(*tray_code)
                queue.enqueue_all(instructions)
                connection.send(bytes("ACK\n", "utf-8"))
            
            elif received_message == "PUT":
                # We need to move to a specific height so the camera can photograph the tray
                queue.enqueue(move_to_camera_position)
                connection.send(bytes("ACK\n", "utf-8"))
        
            else:
                connection.send(bytes("BAD\n", "utf-8"))

        elif not queue.empty():
            connection.send(bytes("BUSY\n", "utf-8"))
        

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
            
            if target_positions_met:

                """
                If the instruction we just fulfilled was "move_to_camera_position" then we 
                need to take a photo of the tray and scan the tray's barcode to determine 
                where we should store it. 
                
                The barcodes contain the trays' [FB][LR][0-4] numbers so we just read that
                data directly and then pass it to the store method to put the trays back.
                """
                if curr_instruction == move_to_camera_position:
                    # We process the image before saving it to disk in case there isn't a tray on the platform
                    # Image directly from webots is in BGRA format for some reason, can just ignore the A
                    image = Image.frombytes("RGB", (1024, 1024), camera.getImage(), "raw", "BGRX")
                    
                    # Read the tray's number from the barcode
                    tray_code = tray_from_barcode(image)

                    if tray_code:
                        # Asterisk here just unpacks the string into a tuple (e.g. store("F", "R", "3"))
                        queue.enqueue_all(store(*tray_code))
                        image.save("images/%s.jpg" % tray_code)
                    else:
                        print("No tray on platform, will not attempt to store.")
                        queue.enqueue(ascend_to_roof)

                # Regardless of what the instruction was, dequeue it now that it has been fulfilled
                queue.dequeue()
                

# Start main loop...
try:
    main_webots_loop()
except KeyboardInterrupt:
    print("Exiting...")
finally:
    # Executes whether or not an exception was caught
    if client_socket:
        client_socket.close()
    server_socket.close()
    image_server.kill()
