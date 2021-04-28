# pyTherma

[![Travis build status](https://travis-ci.org/qris/pytherma.svg?branch=master&status=created)](https://travis-ci.org/github/qris/pytherma)

A Python library and tools for communicating with a Daikin Altherma ASHP
(e.g. model EHBH08CB3V) using serial commands or the P1/P2 bus (with extra
hardware).

This performs a similar underlying function of Daikin's D-Checker software,
i.e. requesting sensor data from a Daikin heat pump, by sending serial commands
to it, and interpreting the response. Unlike D-Checker, it also supports
monitoring the P1/P2 communication bus (with extra hardware).

Unlike D-Checker it does not have a graphical user interface (yet). It is a
library with command-line tools. However the library could be used to make
such an interface.

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

Therefore you use this software (to emulate D-Checker) entirely at your own
risk, and you may void your warranty, destroy your hardware, cause a fire or
emit poisonous gases.

## Hardware Compatibility

You can interface with a Daikin device using either the serial interface
or the P1/P2 bus. In both cases an appropriate adaptor (hardware) is required.

Currently only the following Daikin devices are actually known to be supported:

* [Altherma LT CB EHBH 04/08 CB](https://www.daikin.co.uk/en_gb/products/EHBH-CB.html).

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

Support for new models can be added most easily by downloading an
[ESPAltherma definition file](https://github.com/raomin/ESPAltherma/tree/main/include/def)
for your model, placing it in the `data` directory, and running `poller.py`
with the `--definitions-file` argument pointing to it.

Alternatively, if you don't wish to use the ESPAltherma definition files,
you can:

* Run the D-Checker software to communicate with your device;
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

### P1/P2 Bus

The P1/P2 bus is used by most Daikin user interfaces to control their
equipment.

pyTherma can also communicate with the Daikin by sniffing traffic on this
bus. Again, extra hardware is required: an Arduino running the P1P2Monitor
application, with a P1P2Serial adapter circuit connected to it, and this
connected to the P1/P2 bus. You can buy a pre-assembled adaptor from
Arnold Niessen (author of [P1P2Serial](https://github.com/Arnold-n/P1P2Serial))
and you can find the P1P2Monitor application in the same Github project.

For most devices the meanings of the individual payload
bytes have not yet been determined. See the
[P1P2Serial docs](https://github.com/Arnold-n/P1P2Serial/tree/master/doc)
for more details and current progress.

## Getting Started

Currently you are expected to be a Python developer. You should also create a
virtual environment so that you can run the tests using `tox`, on as many
Python versions as you can get.

### On a Mac

To get a development environment on a Mac using Homebrew:

	brew install python@3.8 python@3.7 pipenv git
	ln -s /usr/local/Cellar/python@3.7/3.7.9/bin/python3.7 /usr/local/bin
	pipenv install
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

To communicate with the Daikin device:

* By serial: `pipenv run python poller --port /dev/ttyUSBx --database '...'`
* By P1/P2: `pipenv run python monitor --port /dev/ttyUSBx --database '...'`

The `--port` should be the Unix device name that the serial hardware
(serial poller) or Arduino (P1/P2 monitor) is connected to.

The `--database` should be a
[SQLAlchemy database URL](https://docs.sqlalchemy.org/en/14/core/engines.html)
to which the software can connect to write down the data received from the
Daikin device. For example, if you are using Postgres, you could use something
like this (substituting your own username, password, server and database name):

    postgresql+psycopg2://<username>:<password>@<server>/<database>

You will need to create the database tables, by passing the `--create`
argument to the application, which will create both tables
(`daikin_serial_state` and `daikin_p1p2_state`).

## Database tables

The structures are defined in `pytherma/sql.py`. There are two tables:

* `daikin_serial_state` (mapped by `SerialState`) contains values read from
  the device's serial interface by `poller.py`.
* `daikin_p1p2_state` (mapped by `P1P2State`) contains values read from
  the P1/P2 bus by `monitor.py`.

### SerialState

This has a simple generic structure, which should support any kind of device
which has ESPAltherma definitions, but requires more work to interpret.
The table has only three columns:

* timestamp: the time that these values were collected.
* raw_page_contents: a JSON mapping from page number (e.g. 0, 96) to the list
  of register values on that page, undecoded. This is mainly useful if you
  change decoding of a register value, and want to fix all previously
  collected data.
* variable_values: a JSON mapping from a unique decoder key to the decoded
  value. The decoder key is of the form `xx.yy.zzz` where `xx` is the register
  page number in hex (2 digits), `yy` is the byte number on that page
  in decimal, and `zzz` is the decoder `convid`.

An example query using this table (in Postgres JSON syntax) is:

    SELECT timestamp,
    dss.variable_values->>'10.0.217' as operation_mode,
    dss.variable_values->>'10.1.304' as defrost,
    dss.variable_values->>'30.0.307' as std_compressor_1,
    dss.variable_values->>'30.0.306' as std_compressor_2,
    dss.variable_values->>'00.1.152' as inv_compressor_qty,
    dss.variable_values->>'00.2.152' as std_compressor_qty,
    dss.variable_values->>'00.3.152' as fan_qty,
    dss.variable_values->>'20.0.105' as outdoor_air_temp,
    dss.variable_values->>'30.0.152' as fan_1,
    dss.variable_values->>'30.1.152' as fan_2,
    dss.variable_values->>'60.2.315' as iu_operation_mode,
    dss.variable_values->>'60.2.303' as thermostat,
    dss.variable_values->>'60.2.302' as freeze_prot,
    dss.variable_values->>'60.2.301' as silent_mode,
    dss.variable_values->>'60.2.300' as freeze_prot_water,
    dss.variable_values->>'60.7.105' as dhw_setpoint,
    dss.variable_values->>'60.9.105' as lwt_setpoint_main,
    dss.variable_values->>'60.12.305' as booster_heater,
    dss.variable_values->>'60.12.306' as three_way_valve_dhw,
    dss.variable_values->>'61.10.105' as dhw_temp,
    dss.variable_values->>'62.2.307' as reheat,
    dss.variable_values->>'62.2.306' as storage_eco,
    dss.variable_values->>'62.2.305' as storage_comfort,
    dss.variable_values->>'62.2.304' as powerful_dhw,
    dss.variable_values->>'62.2.303' as space_heating,
    dss.variable_values->>'62.2.302' as system_off,
    dss.variable_values->>'62.2.301' as unused,
    dss.variable_values->>'62.2.300' as emergency,
    dss.variable_values->>'62.3.105' as lwt_setpoint_add,
    dss.variable_values->>'62.7.304' as main_rt_heating,
    dss.variable_values->>'62.7.306' as additional_rt_heating,
    dss.variable_values->>'62.8.303' as tank_preheat,
    dss.variable_values->>'62.8.302' as circ_pump_running,
    dss.variable_values->>'62.8.301' as alarm_output,
    dss.variable_values->>'62.8.300' as space_heating,
    dss.variable_values->>'62.9.105' as heating_flow_l_min,
    dss.variable_values->>'64.2.301' as bypass_valve,
    dss.variable_values->>'64.3.105' as be_cop,
    dss.variable_values->>'64.9.302' as add_pump,
    dss.variable_values->>'64.9.301' as main_pump,
    dss.variable_values->>'60.12.301' as water_pump_running,
    dss.variable_values->>'21.0.105' as inv_primary_current
    FROM daikin_serial_state dss
    WHERE timestamp >= '2021-04-16 6:00+00'
    AND timestamp <= '2021-04-16 13:00+01'
    AND dss.variable_values->>'60.12.306' = 'true' -- dhw
    ORDER BY "timestamp" ;

### P1P2State

There is currently no generic definition schema that would support any
Daikin device, so I have created a specific one for the most interesting
known fields for my device (EHBH08CB3V):

* timestamp: the time that these values were collected.
* raw_packets_contents: a JSON mapping from packet prefix in hex
  (e.g. `000010`) to the contents of that packet in hex
  (e.g. `0000100101010000000015000000000800001800403700`).
  This is mainly useful if you are figuring out how to decode a new value,
  or you have done so and want to add a new column for it, and populate
  the existing rows from the previously-captured raw data.
* dhw_booster: whether the DHW (hot water) booster heater is enabled (boolean).
* dhw_heating: whether the device is heating DHW (hot water) right now.
* heating_enabled: whether central heating is enabled (by the user on the
  interface control panel).
* heating_on: whether the device is providing central heating right now.
* etc etc. (the column names are fairly self-explanatory).

## Automatic monitoring

You can use the supplied SystemD service files (in the `contrib` directory)
as templates to run these applications automatically, and continuously record
data into the database (for long-term automatic monitoring).

## Library usage

The `pytherma/poller.py` and `pytherma/monitor.py` applications give detailed
examples of how to use the included classes. A very basic usage example is:

    import serial
    import sqlalchemy

    from pytherma.poller import SerialDevice, poll_once
    from pytherma.espaltherma import parse_espaltherma_definition

    definitions_file = 'data/ALTHERMA(LT_CA_CB_04-08KW).h'
    with open(definitions_file) as f:
        definitions_text = f.read()
    decoding_table = parse_espaltherma_definition(definitions_text, output_text=False)

    database_url = 'postgresql+psycopg2://<username>:<password>@<server>/<database>'
    engine = sqlalchemy.create_engine(database_url)
    Base.metadata.create_all(engine)

    raw_serial = serial.Serial(args.port, args.speed, parity=serial.PARITY_EVEN)
    daikin_interface = SerialDevice(raw_serial)
    poll_once(daikin_interface, decoding_table, engine)

## Development

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

### Tests

You should be able to run the tests with:

	pipenv run tox -s

All code contributions should come with tests that exercise them and demonstrate their usage. See
`tests/test_*.py` for examples.

If you're using the Atom editor, you might want to install the `flake8` plugin to pick up any
Lint errors before the tests do. Unfortunately this needs to be installed globally:

  pip3 install flake8
  apm install linter linter-ui-default linter-flake8 intentions busy-signal

## Related Projects

Mainly for controlling other kinds of Daikin devices using different protocols and interfaces:

* [PyDaikin](https://bitbucket.org/mustang51/pydaikin/src/master/) (BRP069A/Bxx, BRP072A/B/Cxx,
  BRP15B61 aka. AirBase, SKYFi).
* [DaikinControl](https://github.com/ael-code/daikin-control) (archived, not maintained,
  Daikin Emura/Caldo).
* [Daikin BRP069](https://bitbucket.org/mustang51/pydaikin/src/master/pydaikin/daikin_brp069.py)
* [P1P2Serial](https://github.com/Arnold-n/P1P2Serial/tree/master/doc)
