"""
Main module of the server file
"""
# System modules
import os
import json
import time
from datetime import datetime

# 3rd party moudles
from flask import render_template, send_from_directory, make_response, abort, send_file
import connexion
import threading
import pathlib

from controller import Robot, LED


# Create a URL route in our application for "/"
# @app.route("/")
# def home():
#     """
#     This function just responds to the browser URL
#     localhost:5000/
#     :return:        the rendered template "home.html"
#     """
#     return render_template("home.html")

"""
This is the tray module which supports some ReST actions for the tray data
"""

target_position = 0

def get_timestamp():
    return datetime.now().strftime(("%Y-%m-%d %H:%M:%S"))

### when run the server we load the data from the stored json files
def load_tray_data():
    trays_dict = dict()
    tray_path = pathlib.Path.cwd() / "trays/"
    for file in os.listdir(tray_path):
        json_data = json.load(open(tray_path / file))
        trays_dict.update({json_data['name']:json_data})
    #print(trays_dict)
    return trays_dict

# whenever TRAYS is updated, we wan't to call this function to update the appropriate file too
def update_tray_json_file(tray_name):
    json_file_path = pathlib.Path.cwd() / "trays" / ("%s.json" % tray_name)
    data = TRAYS.get(tray_name)
    json.dump(data, open(json_file_path, 'w'))


# Data to serve with our API
TRAYS = load_tray_data()


def read_image(tray_name):
    """
    This function responds to a get request for /api/images/{tray_name}
    :param tray_name:   name of tray to find
    :return:            image of tray matching tray_name
    """
    # Does the tray exist?
    if tray_name in TRAYS:
        return send_file(pathlib.Path.cwd() / "images" / ("%s.png" % tray_name)) 

    # otherwise, nope, not found
    else:
        abort(
            404, "Tray with name '{name}' not found".format(name=tray_name)
        )
    
### a wee helper function for the seearch used below
def num_word_matches(search_words, tray_info_words):
            return sum([1 if (word in search_words) else 0 for word in tray_info_words])

def read_all(search):
    """
    This function responds to a request for /api/trays
    with the complete lists of trays
    :param search:  string we use to search and determine the order which we return the trays
    :return:        json string of list of trays
    """
    if search == "":
        print("No searching for items")
        # Create the list of trays from our data
        return [TRAYS[key] for key in sorted(TRAYS.keys())] # return this sorted by tray name i.e. A, B, C ,... or 1, 2, 3, ...
    else:
        search_words = search.split() # get a list of individual words

        # TODO: probably want something which removes any basic word ('a', 'the', ...) from search_words
        #       since these might give loads of unwanted matches in our search

        # get a list of tuples: tray names paired with the number of word matches. Then sort these tuples by the number of matches. 
        # We can then use the order of the names
        # lol Haskell says hello:
        search_ordered_pairs = sorted([(name, num_word_matches(search_words, TRAYS[name]["info"].split())) for name in TRAYS.keys()], key=lambda x:x[1], reverse=True)
        print(search_ordered_pairs)
        return [TRAYS[pair[0]] for pair in search_ordered_pairs] # trays are ordered appropriately


def read_one(name):
    """
    This function responds to a request for /api/trays/{name}
    with one matching tray from TRAYS
    :param name:   name of tray to find
    :return:       tray matching the given name
    """
    
    target_position = float(name)
    
    # Does the tray exist?
    if name in TRAYS:
        tray = TRAYS.get(name)

    # otherwise, nope, not found
    else:
        abort(
            404, "Tray with name {name} not found".format(name=name)
        )

    return tray




def update(name, tray):
    """
    This function updates an existing tray in the tray structure
    :param name:  name of tray to update in the tray structure
    :param tray:  json of what to update the tray to
    :return:      updated tray structure
    """
    # Does the tray exist in TRAYS?
    if name in TRAYS:
        ### the request from the app only has the ability to change 'info' and 'status'
        ### even if they specify other data to change, it won't be used at all
        if tray.get("info") != None:
            TRAYS[name]["info"] = tray.get("info")
            TRAYS[name]["timestamp"] = get_timestamp()
            update_tray_json_file(name)
        if tray.get("status") != None:
            ### actually need to call appropriate function to make the simulation move tray out / store tray
            if tray.get("status") != TRAYS[name]["status"]:
                if tray.get("status") == "out":
                    bring_tray(name)
                if tray.get("status") == "stored":
                    store_tray(name)
                
        return TRAYS[name]

    # otherwise, nope, that's an error
    else:
        abort(
            404, "Tray with name {name} not found".format(name=name)
        )


### helper functions to update appropriate data when storing / bringing trays ----------------

def store_tray(name):
    # originally status = "out"
    print("Storing tray " + name + " ...")
    
    # should now call some function which actually moves the robot appropriately
    # for now I'll just emulate that behaviour with a wait command
    TRAYS[name]["status"] = "moving"
    update_tray_json_file(name)
    time.sleep(5)

    TRAYS[name]["status"] = "stored"
    TRAYS[name]["timestamp"] = get_timestamp()
    update_tray_json_file(name)

def bring_tray(name):
    # originally status = "stored"
    print("Bringing tray " + name + " out ...")

    # check for any tray currently out, and store it first
    for tray_name in TRAYS:
        if TRAYS[tray_name]["status"] == "out":
            print("Tray " + tray_name + " is currently out")
            store_tray(tray_name)

    # now bring the desired tray out
    # should now call some function which actually moves the robot appropriately
    # for now I'll just emulate that behaviour with a wait command
    TRAYS[name]["status"] = "moving"
    update_tray_json_file(name)
    time.sleep(5)
    
    TRAYS[name]["status"] = "out"
    update_tray_json_file(name)

# helper function for threading
def run_app_with_args():
    print("double penis")
    app.run(debug=True, use_reloader=False)

# this runs only when server.py is run from Webots
if __name__ == "__main__":
    # print("penis")
    app = connexion.App(__name__, specification_dir="./")  # specification_dir is just where the swagger.yml lives
    app.add_api("swagger.yml")                             # read the swagger.yml file to configure the endpoints
    threading.Thread(target=app.run).start()     # start flask application in different thread so we can run other code
    
# this runs only when Flask imports server.py from another thread
# global Webots variables should be defined here
if __name__ != "__main__":
    robot = Robot()
    
    vertical_motor = robot.getDevice("vertical motor")
    
    CONTROL_STEP = 64
    
    while True:
        pass
    
    # while robot.step(CONTROL_STEP) != -1:
        # print("arst")
        # vertical_motor.setPosition(target_position)
    
    # led = robot.getDevice("led0")
    # left_wheel = robot.getDevice("left wheel motor")
    # left_wheel.setPosition(float("inf"))
