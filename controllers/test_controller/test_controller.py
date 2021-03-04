"""HORIZONTAL_CONTROLLER controller."""
global keyboardMode
global serverMode
keyboardMode = False
serverMode = True

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
grabSensor = robot.getDevice('grabberPosSensor')
grabSensor.enable(200)


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

def supervise(): #give the robot a command with this function
#TODO: accept enter/retrive commands. maybe make a custom class for it?
    return ["Retrieve", 4, "R", "F"] #dummy result. Retrieve from the forward stack, 4th row, right column



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
      
      
def serverMotion(targetVertVal, targetHoriVal, targetFbVal):
   #define how the robot should receive packets and commands from the server
   vVal = 0
   hVal = 0
   fbVal = 0 #from -0.2 to 0.2
      
   vVal = (targetVertVal - vertPosSensor.getValue())*0.7
   if round(vVal, 3) == 0:
      vVal = 0  
      
   hVal = (targetHoriVal - horiPosSensor.getValue())*0.7
   if vVal != 0 or round(hVal, 3) == 0:
      hVal = 0
      
      
   fbVal = (targetFbVal - grabSensor.getValue())*0.5
   if vVal != 0 or hVal != 0 or round(fbVal, 3) == 0:
       fbVal = 0
  
   # print([vVal, hVal, fbVal])
   return [vVal, hVal, fbVal]

# You should insert a getDevice-like function in order to get the
# instance of a device of the robot. Something like:
#  motor = robot.getMotor('motorname')
#  ds = robot.getDistanceSensor('dsname')
#  ds.enable(timestep)

def retrieve(): #we have to use generators due to timestep shenanigans
   tgv, tgh, tgfb = 0.53, -0.21, 0.166
   while round(vertPosSensor.getValue(), 2) != 0.68 or horiPosSensor.getValue() != 0 or grabSensor.getValue() != 0:
      
      yield [0.68,0,0] #set it to a start position.
   #the robot is now at the start position
   while serverMotion(tgv, tgh, tgfb) != [0,0,0]:
      yield [tgv, tgh, tgfb]
      
   while serverMotion(tgv, tgh, 0) != [0, 0, 0]:
       print("stage: retriever return")
       yield [tgv, tgh, 0] #return the retriever to rest pos
       
   while serverMotion(tgv, 0, 0) != [0, 0, 0]:
       yield [tgv, 0, 0]
   
   while vertPosSensor.getValue() != 1 or horiPosSensor.getValue() != 0 or grabSensor.getValue() != 0:
      yield [0.68,0,0] #set it to a start position.    
    


gen = retrieve()



# Main loop:
#tgv, tgh, tgfb = 0.53, -0.21, 0.2
v,h, fb = 0,0,0
# - perform simulation steps until Webots is stopping the controller
while robot.step(timestep) != -1:
   #print(vertPosSensor.getValue())
   if serverMode == True:
      tgv, tgh, tgfb = next(gen)
      # print([vertPosSensor.getValue(), horiPosSensor.getValue(), grabSensor.getValue()])
      v,h, fb = serverMotion(tgv, tgh, tgfb)
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
