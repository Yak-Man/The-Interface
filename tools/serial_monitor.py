#!/usr/bin/env python3
"""
Plain-text serial monitor for The Interface's Arduino Uno R4 Minima.

Prints every line theinterface.ino sends over serial, with a wall-clock
timestamp, straight to stdout -- run it in VS Code's integrated terminal
(``Ctrl+` `` -> Terminal > New Terminal) to watch live sensor/BPM/HRV/
SpO2/motor output without leaving the editor. That terminal panel *is*
the monitor; no extra VS Code extension is required. This is the
plain-text half of the pair -- see serial_plotter.py for the live-graph
half.

Usage:
    python tools/serial_monitor.py [--port COM9] [--baud 115200]

Doesn't touch theinterface.ino at all -- just reads whatever it already
prints (see printChannel() there).
"""
import argparse
import sys
import time

import serial
import serial.tools.list_ports

DEFAULT_BAUD = 115200
FALLBACK_PORT = "COM9"  # this project's known port on the dev machine -- see the
                         # arduino-cli-connection memory


def find_port():
    """Best-effort auto-detect: the first port whose description looks
    like an Arduino, else FALLBACK_PORT. COM assignments aren't stable
    across reboots/replugs/machines, so --port always wins if given."""
    for p in serial.tools.list_ports.comports():
        desc = (p.description or "").lower()
        if "arduino" in desc or "usb serial" in desc:
            return p.device
    return FALLBACK_PORT


def open_port(port, baud):
    ser = serial.Serial()
    ser.port = port
    ser.baudrate = baud
    ser.timeout = 1
    # The R4 Minima's native-USB CDC serial produces no output unless
    # DTR/RTS are asserted on open -- same as what opening Arduino's own
    # Serial Monitor does under the hood. Skip this and the port opens
    # fine but silently never receives anything, which looks identical
    # to a dead connection. See the arduino-cli-connection memory.
    ser.dtr = True
    ser.rts = True
    ser.open()
    # Asserting DTR resets the board, so give setup() time to finish
    # (sensor init, LED strip init, etc.) before the first read.
    time.sleep(3)
    return ser


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--port", help="Serial port (default: auto-detect, falling back to COM9)")
    parser.add_argument("--baud", type=int, default=DEFAULT_BAUD)
    args = parser.parse_args()

    port = args.port or find_port()
    print(f"Connecting to {port} @ {args.baud} baud...")
    try:
        ser = open_port(port, args.baud)
    except serial.SerialException as e:
        print(f"Could not open {port}: {e}", file=sys.stderr)
        sys.exit(1)

    print(f"Connected. Reading from {port} -- Ctrl+C to stop.\n")
    try:
        while True:
            line = ser.readline().decode("utf-8", errors="replace").rstrip()
            if line:
                print(f"[{time.strftime('%H:%M:%S')}] {line}")
    except KeyboardInterrupt:
        print("\nStopped.")
    finally:
        ser.close()


if __name__ == "__main__":
    main()
