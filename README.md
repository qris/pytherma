# pyTherma

A Python library and tools for communicating with a Daikin Altherma ASHP (e.g. model EHBH08CB3V)
using serial commands.

This performs the underlying function of Daikin's DChecker software, i.e. requesting sensor data
from a Daikin heat pump, by sending serial commands to it, and interpreting the response. Unlike
DChecker it does not have a user interface (yet), as it's just a library. However it could be used
to make such an interface.

As the [D-Checker manual](https://daikinspare.com.ua/download/dchecker/User%20Manual%20D-Checker%20v3400%20EN.pdf)
says, "This software is designed to be used by Daikin service engineers. Use by any other party is prohibited."
Therefore you use this software (to emulate D-Checker) entirely at your own risk, and you may void your warranty,
destroy your hardware, cause a fire or emit poisonous gases.

## Hardware Compatibility

Currently only the following models are actually supported (or believed to be):

* [Altherma LT CB EHBH 04/08 CB](https://www.daikin.co.uk/en_gb/products/EHBH-CB.html).

Other models listed above could be added, if they are compatible with D-Checker, and you
can obtain a copy, and the necessary hardware.

As the [D-Checker manual](https://daikinspare.com.ua/download/dchecker/User%20Manual%20D-Checker%20v3400%20EN.pdf)
says:

According to the [D-Checker manual](https://daikinspare.com.ua/download/dchecker/User%20Manual%20D-Checker%20v3400%20EN.pdf)
it supports (and therefore this software could one day support):

* SkyAir Models manufactured in 2003 and later. (Exceptions may apply; some models do not support
  D-checker protocol. VRVII MA (M9) series are not supported.)
* RA Models manufactured in 2002 and later.
* VRV Models manufactured in 2003 and later. (Maximum supported number of VRV indoor unit data is 59.)
* Altherma LT:BB,CA indoor unit models (2010 and later).

And not chillers, Altherma HT or Altherma Flex.

### Serial interface

You will need the serial interface hardware, such as:

* D-Checker hardware (999495P). This is quite expensive, for example £310 + VAT from
  [Aircon Online](https://aircon-online.co.uk/product/d-checker-for-ducted-units/). It may come with
  a copy of the D-Checker software. I've never seen one come up on Ebay.
* Daikin PC Cable (EKPCCAB4). This is slightly cheaper, only designed for uploading field settings to
  the unit, but it also works with D-Checker software and looks physically identical.
  For example, £241 from [plumbtrades](https://www.plumbtrades.co.uk/product/daikin-pc-cable-ekpccab3/),
  or about £150 on Ebay.
* Bluetooth Service Checker (999172T). I've seen these on Ebay for about $60 plus international
  postage. Technically it's Bluetooth and not serial, but since it connects to the device the same
  way (by serial cable), I think it probably supports the same protocol in some manner over
  Bluetooth (to be confirmed).

### Adding support for new models

Other models listed above could be added, if you:

* Run the D-Checker software to communicate with it;
* Capture a trace of this serial communication;
* Use D-Checker to Record some activity of the unit;
* Export it to CSV;
* Compare the changes in recorded values (e.g. temperatures) with changes in the messages (e.g.
  a byte in the response to a particular command changes value since the last response);
* Implement a decoder entry to extract this value from the response, with a test.
* Ideally, provide autodetect data (the comms when choosing Auto Detect in D-Checker) to help
  identify the unit automatically, and/or confirm the correct unit choice.

You can't just download the D-Checker software (anywhere that I can find; please let me know if you
do) but you may be able to obtain a copy by contacting technicalhelp@daikin.co.uk and asking for the
latest version.

As the [D-Checker manual](https://daikinspare.com.ua/download/dchecker/User%20Manual%20D-Checker%20v3400%20EN.pdf)
says:

* This software is designed to be used by Daikin service engineers. Use
  by any other party is prohibited.
* D-checker is a software application used to record and monitor operation data
  from an air conditioner to which it has been connected with a cable. Be sure to
  read the User Manual before use.
* The software can monitor the status of sensors (temperature and pressure) and
  actuators (compressors, solenoid valves, etc.) on air conditioners.
* The data supported by the software vary by model.
* D-checker collects air conditioner operation data via control PCB connectors on
  outdoor units. Monitoring and recording of data from multiple outdoor unit
  circuits is not supported.

Although the protocol is probably the same, the definition files are encrypted, so we can't just
extract the number, meaning and data type of each variable from them. They must be reverse engineered.

Serial port traces can be captured using HHD Software's
[Free Serial Analyzer](https://freeserialanalyzer.com/). The free version has limitations, including
a maximum recording time of 20 minutes, and a maximum number of recordings per day. However it worked
better than any other option I could find so far. The [DMS Decoder script](bin/dms_txt_parser.py)
can parse the exported command and response files from this software, making reverse engineering
slightly easier.

You might also have some luck with [Eltima Software Serial Port Monitor](https://www.eltima.com/products/serial-port-monitor/)
and/or [SerialMon](https://www.serialmon.com/) (free).

## Usage

Construct a pyTherma object (TBC) using a pyserial interface, and get some values:

	from pytherma.core import Pytherma

	pytherma = Pytherma(serial.Serial('COM3', 9600, timeout=1))
	values = pytherma.poll()
	print(values)
	print(values[144])
	print(values[144].value)

Which outputs something like:

	{144: AttributeValue(number=144, label="Leaving water temp. before BUH (R1T)(C)", value=37.2), ...}
	AttributeValue(number=144, label="Leaving water temp. before BUH (R1T)(C)", value=37.2)
	37.2

If you have Python 3.7 installed, you should be able to run the tests with:

	tox -e py37

## Related Projects

Mainly for controlling other kinds of Daikin devices using different protocols and interfaces:

* [PyDaikin](https://bitbucket.org/mustang51/pydaikin/src/master/) (BRP069A/Bxx, BRP072A/B/Cxx,
  BRP15B61 aka. AirBase, SKYFi).
* [DaikinControl](https://github.com/ael-code/daikin-control) (archived, not maintained,
  Daikin Emura/Caldo).
* [Daikin BRP069](https://bitbucket.org/mustang51/pydaikin/src/master/pydaikin/daikin_brp069.py)

