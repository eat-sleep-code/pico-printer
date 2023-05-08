import os
import machine
import utime
import sdcard
import ssd1306



# Define pins
xIn1Pin = machine.Pin(0, machine.Pin.OUT)
xIn2Pin = machine.Pin(1, machine.Pin.OUT)
xIn3Pin = machine.Pin(2, machine.Pin.OUT)
xIn4Pin = machine.Pin(3, machine.Pin.OUT)
yIn1Pin = machine.Pin(4, machine.Pin.OUT)
yIn2Pin = machine.Pin(5, machine.Pin.OUT)
yIn3Pin = machine.Pin(6, machine.Pin.OUT)
yIn4Pin = machine.Pin(7, machine.Pin.OUT)
zIn1Pin = machine.Pin(8, machine.Pin.OUT)
zIn2Pin = machine.Pin(9, machine.Pin.OUT)
zIn3Pin = machine.Pin(10, machine.Pin.OUT)
zIn4Pin = machine.Pin(11, machine.Pin.OUT)
extruderIn1Pin = machine.Pin(12, machine.Pin.OUT)
extruderIn2Pin = machine.Pin(13, machine.Pin.OUT)
extruderIn3Pin = machine.Pin(14, machine.Pin.OUT)
extruderIn4Pin = machine.Pin(15, machine.Pin.OUT)
extruderRelayPin = machine.Pin(16, machine.Pin.OUT)
heatedBedRelayPin = machine.Pin(17, machine.Pin.OUT)
startStopButtonPin = machine.Pin(18, machine.Pin.IN, machine.Pin.PULL_UP)
oledSclPin = machine.Pin(19)
oledSdaPin = machine.Pin(20)
oledRstPin = machine.Pin(21)

# =============================================================================

# Define motor movement patterns for 28BYJ-48 stepper motor
stepSequence = [
    [1, 0, 0, 0],  # Step 1
    [1, 1, 0, 0],  # Step 2
    [0, 1, 0, 0],  # Step 3
    [0, 1, 1, 0],  # Step 4
    [0, 0, 1, 0],  # Step 5
    [0, 0, 1, 1],  # Step 6
    [0, 0, 0, 1],  # Step 7
    [1, 0, 0, 1]   # Step 8
]


# Define steps per revolution for each stepper motor
xStepsPerRev = 4096  # Adjust as needed
yStepsPerRev = 4096  # Adjust as needed
zStepsPerRev = 4096  # Adjust as needed
extruderStepsPerRev = 4096  # Adjust as needed


# Define motor speed and acceleration
xSpeed = 500  # Steps per second
xAcceleration = 1000  # Steps per second^2
ySpeed = 500  # Steps per second
yAcceleration = 1000  # Steps per second^2
zSpeed = 100  # Steps per second
zAcceleration = 200  # Steps per second^2
extruderSpeed = 100  # Steps per second
extruderAcceleration = 200  # Steps per second^2


# Delay between steps (in microseconds) for each motor
# Adjust these values based on your motor's specifications and desired movement speed
xStepDelay = int(1000000 / xSpeed)
yStepDelay = int(1000000 / ySpeed)
zStepDelay = int(1000000 / zSpeed)
extruderStepDelay = int(1000000 / extruderSpeed)

# =============================================================================

# Define SD card SPI pins
sdCsPin = machine.Pin(5)
sdSckPin = machine.Pin(18)
sdMisoPin = machine.Pin(19)
sdMosiPin = machine.Pin(23)


# Initialize SD card
spi = machine.SPI(1, baudrate=10000000, polarity=0, phase=0, sck=sdSckPin, mosi=sdMosiPin, miso=sdMisoPin)
sd = sdcard.SDCard(spi, sdCsPin)
vfs = os.VfsFat(sd)

# =============================================================================

# Initialize OLED display
i2c = machine.I2C(0, scl=oledSclPin, sda=oledSdaPin)
oled = ssd1306.SSD1306_I2C(128, 64, i2c, addr=0x3C, external_vcc=False, reset=oledRstPin)

# =============================================================================

# Function to find the first GCode file in the folder
def findRecentGCodeFile():
    files = os.listdir("/")
    files = [file for file in files if file.endswith(".gcode")]
    if not files:
        return None
    files = [os.path.join("/", file) for file in files]
    recentFile = max(files, key=os.path.getmtime)
    return recentFile


# Function to process GCode file and move the axis accordingly
def processGCodeFile(filename):
    with open(filename, "r") as file:
        for line in file:
            line = line.strip()
            if line.startswith("G"):
                code = line.split()[0]
                if code == "G1":
                    # Movement command
                    axis = line[1]
                    distance = float(line[2:])
                    move(axis, distance)
                elif code == "M104":
                    # Extruder temperature command
                    temp = float(line[5:])
                    setExtruderTemperature(temp)
                elif code == "M140":
                    # Heated bed temperature command
                    temp = float(line[5:])
                    setHeatedBedTemperature(temp)

# =============================================================================

def setMotor(motor, step):
    if motor == 'X':
        xIn1Pin.value(step[0])
        xIn2Pin.value(step[1])
        xIn3Pin.value(step[2])
        xIn4Pin.value(step[3])
    elif motor == 'Y':
        yIn1Pin.value(step[0])
        yIn2Pin.value(step[1])
        yIn3Pin.value(step[2])
        yIn4Pin.value(step[3])
    elif motor == 'Z':
        zIn1Pin.value(step[0])
        zIn2Pin.value(step[1])
        zIn3Pin.value(step[2])
        zIn4Pin.value(step[3])
    elif motor == 'E':
        extruderIn1Pin.value(step[0])
        extruderIn2Pin.value(step[1])
        extruderIn3Pin.value(step[2])
        extruderIn4Pin.value(step[3])

		
def move(axis, distance):
    stepsPerRev = {
        'X': xStepsPerRev,
        'Y': yStepsPerRev,
        'Z': zStepsPerRev,
        'E': extruderStepsPerRev
    }
    speed = {
        'X': xSpeed,
        'Y': ySpeed,
        'Z': zSpeed,
        'E': extruderSpeed
    }
    acceleration = {
        'X': xAcceleration,
        'Y': yAcceleration,
        'Z': zAcceleration,
        'E': extruderAcceleration
    }
    stepDelay = {
        'X': xStepDelay,
        'Y': yStepDelay,
        'Z': zStepDelay,
        'E': extruderStepDelay
    }
    motorPins = {
        'X': stepSequence,
        'Y': stepSequence,
        'Z': stepSequence,
        'E': stepSequence
    }

    motor = axis.upper()
    steps = int(distance * stepsPerRev[motor])
    motorSteps = motorPins[motor]
    speedVal = speed[motor]
    accelerationVal = acceleration[motor]
    
    delay = stepDelay[motor]

    for _ in range(steps):
        for step in motorSteps:
            setMotor(motor, step)
            utime.sleep_us(delay)

# =============================================================================

# Function to set the extruder temperature
def setExtruderTemperature(temp):
    # Code to control the extruder relay to heat or maintain temperature
    if temp > 0:
        extruderRelayPin.value(1)  # Turn on the extruder heater
        print("Heating extruder to " + str(temp) + "C")
    else:
        extruderRelayPin.value(0)  # Turn off the extruder heater
        print("Turning off extruder heater")

# =============================================================================

# Function to set the heated bed temperature
def setHeatedBedTemperature(temp):
    # Code to control the heated bed relay to heat or maintain temperature
    if temp > 0:
        heatedBedRelayPin.value(1)  # Turn on the heated bed
        print("Heating bed to " + str(temp) + "C")
    else:
        heatedBedRelayPin.value(0)  # Turn off the heated bed
        print("Turning off heated bed")
     
# =============================================================================

def handleStartStopButton():
    if startStopButtonPin.value() == 0:
        # Button is pressed
        if printerState == "idle":
            # Start printing the most recent GCode file
            gcodeFile = findRecentGCodeFile()
            if gcodeFile:
                writeStatus("Starting to print: " + gcodeFile)
                processGCodeFile(gcodeFile)
                # Set printer state to "printing"
                printerState = "printing"
        elif printerState == "printing":
            # Button is held for 5 seconds to stop printing
            startTime = utime.time()
            while startStopButtonPin.value() == 0:
                if utime.time() - startTime >= 5:
                    writeStatus("Stopping...")
                    setExtruderTemperature(0)
                    setHeatedBedTemperature(0)
                    printerState = "idle"
                    break
    else:
        # Button is not pressed
        # Reset any state variables or flags if needed
        pass
	
# =============================================================================

# Function to write status messages to the OLED display and console
def writeStatus(message):
    # Write to OLED display
    oled.fill(0)  # Clear the display
    oled.text(message, 0, 0)
    oled.show()
    # Write to console
    print(message)

# =============================================================================
	

	
printerState = "idle"
while True:
    handleStartStopButton()
    # Other code or tasks to run in the main loop
    
    # Example: Writing status messages to OLED display and console
    if printerState == "idle":
        writeStatus("Printer is idle")
    elif printerState == "printing":
        writeStatus("Printing in progress")
    else:
        writeStatus("Unknown state")
