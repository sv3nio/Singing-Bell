# Built-in
import board
import ipaddress
import microcontroller
import os
import pwmio
import socketpool
import time
import wifi
import json
import asyncio

# External
from adafruit_httpserver.server import HTTPServer
from adafruit_httpserver.request import HTTPRequest
from adafruit_httpserver.response import HTTPResponse
from adafruit_httpserver.methods import HTTPMethod
from adafruit_httpserver.mime_type import MIMEType
from adafruit_motor import servo


# SETTINGS!
mallet_pin      = board.A0                                  # Mallet Pin
gateway_ip      = "0.0.0.0"                                 # IP address of your router/gateway
ipv4            = ipaddress.IPv4Address("0.0.0.0")          # The static IP for this device
netmask         = ipaddress.IPv4Address("255.255.255.0")    # Network Mask. Defaults to 255.255.255.0
calib_angle     = 165                                       # The angle at which to position the bowl

print("\n###################################\n#  Starting Up Singing Bowl Bell  #\n###################################")

# VARs & Objects
pwm         = pwmio.PWMOut(mallet_pin, duty_cycle=2 ** 15, frequency=50)
mallet      = servo.Servo(pwm)
gateway     = ipaddress.IPv4Address(gateway_ip)
pool        = socketpool.SocketPool(wifi.radio)
server      = HTTPServer(pool)
ready_angle = calib_angle - 10
mid_angle   = calib_angle - 5
chime_angle = calib_angle + 10

class ChimeManager:
  def __init__(self, type, action, status):
    self.type = type
    self.action = action
    self.status = status

chime_manager = ChimeManager("None", "None", "idle")

#  Connect to WiFi
try:
    print("\nConnecting to WiFi...")
    wifi.radio.hostname = "singing-bell"
    wifi.radio.set_ipv4_address(ipv4=ipv4,netmask=netmask,gateway=gateway)
    wifi.radio.connect(os.getenv('CIRCUITPY_WIFI_SSID'), os.getenv('CIRCUITPY_WIFI_PASSWORD'))
    print("Connected to {}.".format(wifi.radio.ap_info.ssid))
except:
    print("Critical error during Wifi connection attempt! Rebooting...")
    time.sleep(3)
    microcontroller.reset()

def send_response(request, data):
    with HTTPResponse(request, content_type=MIMEType.TYPE_JSON) as response:
        response.send(json.dumps(data))


# HTTP Server Routes
@server.route("/api/status", "GET")  # Example: /api/status
def status_api(request: HTTPRequest):
    send_response(request, {"type": chime_manager.type,
                            "action": chime_manager.action,
                            "status": chime_manager.status})

@server.route("/api/calibrate", "PUT") # Example: /api/calibrate?angle=165 
def calibrate(request: HTTPRequest):
    test_angle = request.query_params.get("angle")

    # TO DO: 
    # - Validate test_angle range X-Y (negative values?)
    # - Datatype (int) error feedback

    if test_angle:
        try:
            mallet.angle = int(test_angle)
        except:
            return
        print("\nBeginning mallet calibration sequence...")
        print(" --> Mallet is in position for the next 10 seconds.\n --> Use this time to adjust the position of the bowl.")
        time.sleep(10)
        mallet.angle = ready_angle
        print("Calibration sequence complete.")
    else:
        print("\nBeginning mallet calibration sequence...")
        for angle in range(ready_angle, calib_angle, 1):
            mallet.angle = angle
            time.sleep(0.05)
        print(" --> Mallet is in position for the next 10 seconds.\n --> Use this time to adjust the position of the bowl.")
        time.sleep(10)
        for angle in range(calib_angle, ready_angle, -1):
            mallet.angle = angle
            time.sleep(0.05)
        print("Calibration sequence complete.")

    send_response(request, {"type": "calibrate",
                        "action": "stop",
                        "status": "idle"})


@server.route("/api/chime", "PUT")         # Example: /api/chime?type= [ alarm | meditate | doorbell ] &action= [ start | stop ] 
def chime_api(request: HTTPRequest):
    type = request.query_params.get("type")
    action = request.query_params.get("action")

    # Validate type parameter
    if type != "alarm" or type != "meditate" or type != "doorbell":
        return

    # Validate action parameter
    if action == "start":
        chime_manager.status = "chiming"
    elif action == "stop":
        chime_manager.status = "idle"
    else:
        return

    chime_manager.type = type
    chime_manager.action = action 

    send_response(request, {"type": chime_manager.type,
                            "action": chime_manager.action,
                            "status": chime_manager.status})


async def server_task():
    clock = time.monotonic()

    # Initialize mallet position
    mallet.angle = ready_angle

    # Start HTTP server
    try:
        print("\nStarting HTTP server...")
        server.start(str(wifi.radio.ipv4_address))
        print("Ready! Listening on: http://{}".format(wifi.radio.ipv4_address))
    except :
        print("\n\nCritical error during HTTP server startup! Rebooting...")
        time.sleep(3)
        microcontroller.reset()

    while True:
        await asyncio.sleep(0.1)
        try:
            # Connectivity check every 2 min. Reboot if disconnected.
            if (clock + 120) < time.monotonic():
                clock = time.monotonic()
                if wifi.radio.ping(gateway, timeout=3.0) is None:
                    print("\n\nPing Timeout Error!! Rebooting...")
                    microcontroller.reset()
                
            # Poll for HTTP connections
            server.poll()

        except Exception as e:
            print(e)
            continue


async def chimer_task():
    while True:
        await asyncio.sleep(0.1)

        # Wake-up Alarm
        # Instead of a while loop, the wake-up alarm block uses a range counter to prevent the
        # bell from chiming indefinitely in case a "stop" command doesn't arrive.
        if chime_manager.type == "alarm" and chime_manager.action == "start":
            for _ in range(10):
                if chime_manager.type == "alarm" and chime_manager.action == "stop":
                    break
                mallet.angle = mid_angle
                time.sleep(0.03)
                mallet.angle = chime_angle
                time.sleep(0.02)
                mallet.angle= mid_angle
                await asyncio.sleep(1)
                for angle in range(mid_angle, ready_angle, -1):
                    mallet.angle = angle
                    time.sleep(0.05)
                await asyncio.sleep(7)

            # Discontinue chiming if no "stop" command arrives
            chime_manager.action = "stop"
            chime_manager.status = "idle"
        
        # Meditate
        while chime_manager.type == "meditate" and chime_manager.action == "start":
            mallet.angle = mid_angle
            time.sleep(0.03)
            mallet.angle = chime_angle
            time.sleep(0.02)
            mallet.angle = mid_angle
            await asyncio.sleep(1)
            for angle in range(mid_angle, ready_angle, -1):
                mallet.angle = angle
                time.sleep(0.05)
            await asyncio.sleep(15)

        # Doorbell
        while chime_manager.type == "doorbell" and chime_manager.action == "start":
            # First strike
            mallet.angle = mid_angle
            time.sleep(0.03)
            mallet.angle = chime_angle
            time.sleep(0.02)
            # Second strike
            mallet.angle = mid_angle
            await asyncio.sleep(0.3)
            mallet.angle = chime_angle
            time.sleep(0.02)
            mallet.angle = mid_angle
            # Return to ready_angle
            for angle in range(mid_angle, ready_angle, -1):
                mallet.angle = angle
                time.sleep(0.05)
            chime_manager.action = "stop"
            chime_manager.status = "idle"
            await asyncio.sleep(3)

async def main():
    server_tasker = asyncio.create_task(server_task())
    chimer_tasker = asyncio.create_task(chimer_task())
    await asyncio.gather(server_tasker, chimer_tasker)

asyncio.run(main())
