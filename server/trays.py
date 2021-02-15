"""
This is the people module and supports all the ReST actions for the
PEOPLE collection
"""

# System modules
from datetime import datetime

# 3rd party modules
from flask import make_response, abort, send_file


def get_timestamp():
    return datetime.now().strftime(("%Y-%m-%d %H:%M:%S"))



# Data to serve with our API
# should have these actually stored as json files
# whenever TRAYS is updated, the appropriate .json file is also updated
TRAYS = {
    "A": {
        "name": "A",
        "info": "blah blah blah stuff, more stuff",
        "currently out" : "no",
        "capacity" : "0.5",
        "timestamp" : get_timestamp(),
    },
    "B": {
        "name": "B",
        "info": "random stuff",
        "currently out" : "no",
        "capacity" : "0.2",
        "timestamp" : get_timestamp(),
    },
    "C": {
        "name": "C",
        "info": "",
        "currently out" : "Yes",
        "capacity" : "1.0",
        "timestamp" : get_timestamp(),
    },
}


def read_image(tray_name):
    """
    This function responds to a get request for /api/images/{tray_name}
    :param tray_name:   name of tray to find
    :return:            image of tray matching tray_name
    """
    # Does the tray exist?
    if tray_name in TRAYS:
        return send_file("/home/andrew/Documents/SDP/server/images/" + tray_name + ".png")

    # otherwise, nope, not found
    else:
        abort(
            404, "Tray with name '{name}' not found".format(name=tray_name)
        )
    

def read_all():
    """
    This function responds to a request for /api/trays
    with the complete lists of trays
    :return:        json string of list of trays
    """
    # Create the list of people from our data
    return [TRAYS[key] for key in sorted(TRAYS.keys())]


def read_one(name):
    """
    This function responds to a request for /api/trays/{name}
    with one matching tray from TRAYS
    :param name:   name of tray to find
    :return:       tray matching the given name
    """
    # Does the person exist in people?
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
        ### the request from the app only has the ability to change 'info' and 'currently out'
        ### even if they specify other data to change, it won't be used at all
        if tray.get("info") != None:
            TRAYS[name]["info"] = tray.get("info")

        if tray.get("currently out") != None:
            ### actually need to call appropriate function to make the simulation move tray out / store tray
            if tray.get("currently out") != TRAYS[name]["currently out"]:
                if tray.get("currently out") == "yes":
                    print("Bringing tray " + name + " out")
                if tray.get("currently out") == "no":
                    print("Storing tray " + name)
                
                TRAYS[name]["currently out"] = tray.get("currently out")

            ### might need to move other tray into storage first (and also update its appropriate TRAYS entry)
        TRAYS[name]["timestamp"] = get_timestamp()
        return TRAYS[name]

    # otherwise, nope, that's an error
    else:
        abort(
            404, "Tray with name {name} not found".format(name=name)
        )


# SHOULDN'T NEED THESE 2, these are still just the copied things from a 'people' database
def create(person):
    """
    This function creates a new person in the people structure
    based on the passed in person data
    :param person:  person to create in people structure
    :return:        201 on success, 406 on person exists
    """
    lname = person.get("lname", None)
    fname = person.get("fname", None)

    # Does the person exist already?
    if lname not in PEOPLE and lname is not None:
        PEOPLE[lname] = {
            "lname": lname,
            "fname": fname,
            "timestamp": get_timestamp(),
        }
        return make_response(
            "{lname} successfully created".format(lname=lname), 201
        )

    # Otherwise, they exist, that's an error
    else:
        abort(
            406,
            "Person with last name {lname} already exists".format(lname=lname),
        )

def delete(lname):
    """
    This function deletes a person from the people structure
    :param lname:   last name of person to delete
    :return:        200 on successful delete, 404 if not found
    """
    # Does the person to delete exist?
    if lname in PEOPLE:
        del PEOPLE[lname]
        return make_response(
            "{lname} successfully deleted".format(lname=lname), 200
        )

    # Otherwise, nope, person to delete not found
    else:
        abort(
            404, "Person with last name {lname} not found".format(lname=lname)
        )

