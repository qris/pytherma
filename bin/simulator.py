""" Simulates a Daikin device.

Reads serial commands (presumably from D-Checker) and responds to them. """

from pytherma.simulator import device_simulator

if __name__ == '__main__':
    device_simulator()
