# Singing Bell

An API-enabled singing bowl robot for wake-up alarm, doorbell and meditation. Powered by CircuitPython.

<img alt="Singing Bell Demo" src="/img/singing-bell-a.jpg" width="400">

# Usage
This is an advanced project requiring skills in: microelectronics, Python programming, application design and 3D printing. A working implementation will need:

- A CircuitPython compatible microcontroller running [CircuitPython 8 or higher](https://circuitpython.org/). Get libraries from [here](https://github.com/adafruit/circuitpython).
- A 5v servo motor to swing the mallet (or comparable alternative).
- A manufactured housing of some kind (3D print models are on [Tinkercad](https://www.tinkercad.com/things/ihloFZPHmth?sharecode=iWwOf8UDUHXrbG2nKjJkbB91yBh4DRdOCrIBXainu0E)).
- A client app to make the things go.
- A super-awesome singing bowl! 😉

⚠️ IMPORTANT ⚠️  
This project does not provide a user interface for controlling the bell. Instead, it provides a web API for use with another app or frontend. *You will need to write your own client application to use this project.* Presently, I'm using a [surprisingly good!] quick-and-dirty solution on my Android device (Tasker) with future designs for a more robust server frontend.

## Servo Motor
The solution works by striking the singing bowl with its proper mallet attached to a servo motor. Frankly, any 5v servo should suffice, just make sure to configure the appropriate pin in `main.py`:

```
  mallet_pin = board.A0
```

## Calibration
Servo motors aren't smart, so the unit won't know how far away the mallet is from the singing bowl at any given time. To address this, the unit needs an appropriate calibration angle so it knows which position will strike the bowl. This value is used to calculate more precise angles that do the actual striking:

```
  calib_angle  = 165
```

## Network
To work, the unit will need to connect to a WiFi network and be configured with a static IP. Update `settings.toml` to connect the device to WiFi and the following lines in `main.py` to configure the IP:

```
  gateway_ip   = "0.0.0.0"
  ipv4         = ipaddress.IPv4Address("0.0.0.0")
  netmask      = ipaddress.IPv4Address("255.255.255.0")
```
## API Reference

### Status
Queries the unit for its current status, returns a simple JSON array.

```
  /api/status
```

### Calibration
Initiates a 10 second calibration sequence. If the `angle` parameter (int) is supplied the unit will position the mallet to the specified angle. Omitted, the unit will use the default (internal) calibration angle. Returns a status acknowledgement.

```
  /api/calibrate [ ?angle= [angle] ]
```

### Chiming
Initiates the requested chiming action and returns a status acknowledgement. Chime intervals are statically encoded and will need to be customized to accomodate the individual project. Each chime type has its own behaviours:

- `meditate` requires both `start` and `stop` action commands. Without explicit stopping, it will chime indefintely.
- `alarm` requires only the `start` action, but will honour `stop` when received. Without a `stop` instruction, the unit will automatically stop the wake-up alarm sequence after 10 chimes (~70 seconds). This is customizable.
- `doorbell` requires only `start` and will stop on its own (ignores `stop`). 

```
  /api/chime?type= [ alarm | meditate | doorbell ] &action= [ start | stop ] 
```

## TO DO

- [Bearer token auth](https://docs.circuitpython.org/projects/httpserver/en/latest/examples.html#authentication) to prevent authorized access.
- Better input validation and error handling. Currently, invalid input is silently ignored.
