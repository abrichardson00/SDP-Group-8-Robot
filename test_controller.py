"""HORIZONTAL_CONTROLLER controller."""
global keyboardMode
global serverMode
keyboardMode = True
serverMode = False

# You may need to import some classes of the controller module. Ex:
#  from controller import Robot, Motor, DistanceSensor
from controller import Robot, Motor, Keyboard, Brake, PositionSensor

# create the Robot instance.
robot = Robot()

speed = 0.1
rackAndPinionV = robot.getDevice('vertical motor')
rackAndPinionH = robot.getDevice('horizontal motor')
leftGrab = robot.getDevice('left grabber motor')
rightGrab = robot.getDevice('right grabber motor')

vertPosSensor = robot.getDevice('VertPos')
vertPosSensor.enable(200)
horiPosSensor = robot.getDevice('HoriPos')
horiPosSensor.enable(200)


rackAndPinionH.setPosition(0)
rackAndPinionV.setPosition(0)
#frontBackMotor.setPosition(0)
leftGrab.setPosition(0)
rightGrab.setPosition(0)


#.setPosition(10.0)
rackAndPinionH.setPosition(float('inf'))
rackAndPinionV.setPosition(float('inf'))
#frontBackMotor.setPosition(float('inf'))
leftGrab.setPosition(float('inf'))
rightGrab.setPosition(float('inf'))


#vertRack.setPosition(float('inf'))
#vertRack.setVelocity(speed)
rackAndPinionH.setVelocity(0)
rackAndPinionV.setVelocity(0)
#frontBackMotor.setVelocity(0)
leftGrab.setVelocity(0)
rightGrab.setVelocity(0)

# get the time step of the current world.
timestep = int(robot.getBasicTimeStep())


keyboard = Keyboard()
keyboard.enable(timestep)



def keyboardMotion():
   vVal = 0
   hVal = 0
   fbVal = 0
   key = keyboard.getKey()
   if (key == Keyboard.UP):
        #breakV.setDampingConstant(0.0)
       #rackAndPinionV.setVelocity(speed)
       vVal = speed
   elif (key == Keyboard.DOWN):
        #breakV.setDampingConstant(0.0)
     #rackAndPinionV.setVelocity(-1 * speed)
     vVal = -speed
   else:
      #rackAndPinionV.setVelocity(0)
      vVal = 0
        
   if (key == Keyboard.RIGHT):
        #breakH.setDampingConstant(0.0)
      #rackAndPinionH.setVelocity(speed)
      hVal = speed
   elif(key == Keyboard.LEFT):
        #breakH.setDampingConstant(0.0)
      hVal = -speed
      #rackAndPinionH.setVelocity(-1 * speed)
   else:
      hVal = 0
      #rackAndPinionH.setVelocity(0)
      
   if (key == ord('W')):
      fbVal = speed
   elif (key == ord('S')):
      fbVal = -speed
   else:
      fbVal = 0
      
   return [vVal, hVal, fbVal]
      
      
def serverMotion():
   #define how the robot should receive packets and commands from the server
   targetVertVal = 0.6
   targetHoriVal = 0.6
   vVal = 0
   hVal = 0
   frontBack = 1 #1 for front, 0 for back
   """
   if vertPosSensor.getValue() < targetVertVal:
      #rackAndPinionV.setVelocity(speed)
      vVal = 1
   elif vertPosSensor.getValue() > targetVertVal:
      #rackAndPinionV.setVelocity(-1 * speed)
      vVal = -1
   else:
      vVal = 0
      #rackAndPinionV.setVelocity(0)
      """
      
   vVal = (targetVertVal - vertPosSensor.getValue())*0.5
   if round(vVal, 3) == 0:
      vVal = 0  
      
   """
   if horiPosSensor.getValue() < targetHoriVal:
      #rackAndPinionV.setVelocity(speed)
      hVal = 1
   elif vertPosSensor.getValue() > targetVertVal:
      #rackAndPinionV.setVelocity(-1 * speed)
      hVal = -1
   else:
      hVal = 0
      #rackAndPinionV.setVelocity(0)
   """
   hVal = (targetHoriVal - horiPosSensor.getValue())*0.5
   if round(hVal, 3) == 0:
      hVal = 0
   return [vVal, hVal]

# You should insert a getDevice-like function in order to get the
# instance of a device of the robot. Something like:
#  motor = robot.getMotor('motorname')
#  ds = robot.getDistanceSensor('dsname')
#  ds.enable(timestep)

# Main loop:
v,h, fb = 0,0,0
# - perform simulation steps until Webots is stopping the controller
while robot.step(timestep) != -1:
   #print(vertPosSensor.getValue())
   if serverMode == True:
      v,h = serverMotion()
   elif keyboardMode == True:
      v,h,fb = keyboardMotion()
   else:
      pass
      
   rackAndPinionV.setVelocity(v)
   rackAndPinionH.setVelocity(h)
   leftGrab.setVelocity(fb)
   rightGrab.setVelocity(fb)
   #frontBackMotor.setVelocity(fb)
    #if(key != Keyboard.LEFT || key != Keyboard.RIGHT):
        #breakH.setDampingConstant(10.0)
    # Read the sensors:
    # Enter here functions to read sensor data, like:
    #  val = ds.getValue()

    # Process sensor data here.

    # Enter here functions to send actuator commands, like:
    #  motor.setPosition(10.0)




# Enter here exit cleanup code.
