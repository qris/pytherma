# pyTherma

[![Travis build status](https://travis-ci.org/qris/pytherma.svg?branch=master&status=created)](https://travis-ci.org/github/qris/pytherma)

A Python library and tools for communicating with a Daikin Altherma ASHP (e.g. model EHBH08CB3V)
using serial commands.

This performs the underlying function of Daikin's D-Checker software, i.e. requesting sensor data
from a Daikin heat pump, by sending serial commands to it, and interpreting the response. Unlike
DChecker it does not have a user interface (yet), as it's just a library. However it could be used
to make such an interface.

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

Therefore you use this software (to emulate D-Checker) entirely at your own risk, and you may void your warranty,
destroy your hardware, cause a fire or emit poisonous gases.

## Hardware Compatibility

Currently only the following models are actually supported (or believed to be):

* [Altherma LT CB EHBH 04/08 CB](https://www.daikin.co.uk/en_gb/products/EHBH-CB.html).

Other models listed above could be added, if they are compatible with D-Checker, and you
can obtain a copy, and the necessary hardware.

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
* The [ESPAltherma](https://github.com/raomin/ESPAltherma) project has communicated directly with the
  Daikin, not using any interface or level converter, just an Arduino.

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

Although the protocol is probably the same, the definition files that come with
D-Checker are encrypted, so we can't just extract the number, meaning and data
type of each variable from them. They must be reverse engineered.
[ESPAltherma](https://github.com/raomin/ESPAltherma) appear to have done this already, for example
see the [definitions for Altherma LT/CA and CB](https://github.com/raomin/ESPAltherma/blob/main/include/def/ALTHERMA(LT_CA_CB_04-08KW).h)
and [register description wiki page](https://github.com/raomin/ESPAltherma/wiki/Information-about-Values).

If you do want/need to reverse engineer the registers,
serial port traces can be captured using HHD Software's [Free Serial
Analyzer](https://freeserialanalyzer.com/). The free version has limitations,
including a maximum recording time of 20 minutes, and a maximum number of
recordings per day, and only a 7 day free trial. However it worked better than
any other option I could find so far.  The [DMS Decoder
script](bin/dms_txt_parser.py) can parse the exported command and response
files from this software, making reverse engineering slightly easier.

You might also have some luck with [Eltima Software Serial Port Monitor](https://www.eltima.com/products/serial-port-monitor/)
and/or [SerialMon](https://www.serialmon.com/) (free).

## Getting Started

Currently you are expected to be a Python developer. You should also create a
virtual environment so that you can run the tests using `tox`, on as many
Python versions as you can get.

### On Linux/Mac

To get a development environment on a Mac using Homebrew:

	brew install python@3.8 python@3.7 pipenv git
	ln -s /usr/local/Cellar/python@3.7/3.7.9/bin/python3.7 /usr/local/bin
	pipenv install
	pipenv run tox -s

On Linux, you will need to install Python 3, pipenv, and the Postgres libraries
for development (for [reasons described
here](https://www.psycopg.org/docs/install.html)). For example, on Debian-based systems:

	sudo apt install pipenv git libpq-dev
	pipenv install [--python `which python3`]
	pipenv run tox -s

### On Windows

To get a development environment on Windows using Anaconda:

* Install [Miniconda](https://docs.conda.io/projects/conda/en/latest/user-guide/install/windows.html).
* Open the Anaconda Prompt.
* Install Git with `conda install git`
* Install [Pipenv](https://anaconda.org/conda-forge/pipenv) with `conda install -c conda-forge pipenv`
* Clone the [pyTherma Git repo](https://github.com/qris/pytherma) and enter the directory.
* Create the virtual environment with `pipenv install`

To use it:

* Open the Anaconda Prompt.
* Enter the cloned source code directory.
* Enter the virtual environment with `pipenv run cmd` (`pipenv shell` is a
  [bit broken](https://github.com/pypa/pipenv/issues/876)).

To test the simulator using D-Checker:

* Install [com0com](http://com0com.sourceforge.net/) (a virtual null modem cable for Windows)
* Run its `setup` application and check the names of the auto-generated null modem COM ports
  (e.g. `COM3` and `COM4)``.
* Run the simulator on one of them: `python bin\simulator.py COM4`
* Open D-Checker, open Options, and choose the other one as the COM Port (e.g. `COM3`).
* Choose *Recording*, *REC Only* and click *Altherma (F6)*.
* Choose the appropriate *Data label file* for your model, and click *OK*.

D-Checker should start sending command packets to the simulator, getting responses, and drawing
graphs, although the variable values are not really changing so you won't see much.



## Tests

All code contributions should come with tests that exercise them and demonstrate their usage. See
`tests/test_*.py` for examples.

If you're using the Atom editor, you might want to install the `flake8` plugin to pick up any
Lint errors before the tests do. Unfortunately this needs to be installed globally:

	pip3 install flake8
	apm install linter linter-ui-default linter-flake8 intentions busy-signal

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
* [P1P2Serial](https://github.com/Arnold-n/P1P2Serial/tree/master/doc)
