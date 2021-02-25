"""HORIZONTAL_CONTROLLER controller."""

# You may need to import some classes of the controller module. Ex:
#  from controller import Robot, Motor, DistanceSensor
from controller import Robot, Motor, Keyboard, Brake
import test
import server

# create the Robot instance.
robot = Robot()

speed = 0.5
rackAndPinionV = robot.getDevice('vertical linear motor')
rackAndPinionH = robot.getDevice('horizontal linear motor')


rackAndPinionH.setPosition(0)
rackAndPinionV.setPosition(0)
#.setPosition(10.0)
rackAndPinionH.setPosition(float('inf'))
rackAndPinionV.setPosition(float('inf'))
#vertRack.setPosition(float('inf'))
#vertRack.setVelocity(speed)
rackAndPinionH.setVelocity(0)
rackAndPinionV.setVelocity(0)

# get the time step of the current world.
timestep = int(robot.getBasicTimeStep())


keyboard = Keyboard()
keyboard.enable(timestep)

# You should insert a getDevice-like function in order to get the
# instance of a device of the robot. Something like:
#  motor = robot.getMotor('motorname')
#  ds = robot.getDistanceSensor('dsname')
#  ds.enable(timestep)

# Main loop:
# - perform simulation steps until Webots is stopping the controller
while robot.step(timestep) != -1:
    key = keyboard.getKey()
    if (key == Keyboard.UP):
        #breakV.setDampingConstant(0.0)
        rackAndPinionV.setVelocity(speed)
    elif (key == Keyboard.DOWN):
        #breakV.setDampingConstant(0.0)
        rackAndPinionV.setVelocity(-1 * speed)
    else:
        rackAndPinionV.setVelocity(0)
        
    if (key == Keyboard.RIGHT):
        #breakH.setDampingConstant(0.0)
        rackAndPinionH.setVelocity(speed)
    elif(key == Keyboard.LEFT):
        #breakH.setDampingConstant(0.0)
        rackAndPinionH.setVelocity(-1 * speed)
    else:
        rackAndPinionH.setVelocity(0)
        
        
    #if(key != Keyboard.LEFT || key != Keyboard.RIGHT):
        #breakH.setDampingConstant(10.0)
    # Read the sensors:
    # Enter here functions to read sensor data, like:
    #  val = ds.getValue()

    # Process sensor data here.

    # Enter here functions to send actuator commands, like:
    #  motor.setPosition(10.0)
    pass

# Enter here exit cleanup code.
