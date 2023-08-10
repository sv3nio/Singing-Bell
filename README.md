# Singing Bell

An API-enabled singing bowl robot for wake-up alarm, doorbell and meditation. Powered by CircuitPython.

<img alt="Singing Bell Demo" src="/img/singing-bell-a.jpeg" width="400">

# Usage

**IMPORTANT**
This project does not provide a user interface for controlling the bell. Instead, it provides an API for use with another app or frontend. Presently, our home uses a quick-and-dirty solution on my Android device (Tasker) as an alarm/meditation app with future designs for a more robust server frontend.

#### Servo Motor
The solution works by striking the singing bowl with its proper mallet attached to a servo motor. Frankly, any 5v servo should suffice, just make sure to configure the appropriate pin in `main.py`:

```
    mallet_pin = board.A0
```

#### Calibration
Servo motors aren't smart, so the unit does not know how far away the mallet is from the singing bowl at any given time. To address this, the unit needs an appropriate calibration angle so it knows which position will strike the bowl. This value is used to calculate more precise ready, middle and chiming angles:

```
    calib_angle  = 165
```

#### Network
To work, the unit will need to connect to a WiFi network and be configured with a static IP. Update `settings.toml` to connect the device to WiFi and the following lines in `main.py` to configure the IP:

```
    gateway_ip   = "0.0.0.0"
    ipv4         = ipaddress.IPv4Address("0.0.0.0")
    netmask      = ipaddress.IPv4Address("255.255.255.0")
```
#### API Reference

**Status**
Queries the unit for its current status, returns a simple JSON array.

```
/api/status
```

**Calibration**
Initiates a 10 second calibration sequence. If the `angle` parameter (int) is supplied the unit will position the mallet to the specified angle. Omitted, the unit will use the default (internal) calibration angle. Returns a status report.

```
/api/calibrate [ ?angle= [angle] ]
```

**Chiming**
Initiates the requested chiming action. Chime intervals are statically encoded and will need to be customized to accomodate the installation (i.e. not configurable via API). `alarm` and `meditate` types require both `start` and `stop` action commands whereas `doorbell` requires only `start` and will stop on its own. Returns a status report.

```
/api/chime?type= [ alarm | meditate | doorbell ] &action= [ start | stop ] 
```

## TO DO

- [Bearer token auth](https://docs.circuitpython.org/projects/httpserver/en/latest/examples.html#authentication) to prevent authorized access.
- Better input validation and error handling. Currently, invalid input is silently ignored.
