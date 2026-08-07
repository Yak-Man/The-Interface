# %% [markdown]
# # The Interface — Live Serial Plotter
#
# Run this file's cells in VS Code (Python extension, `ms-python.python`
# -- recommended automatically for this workspace, see
# `.vscode/extensions.json`): open this file, then "Run Cell" on each
# `# %%` block below in order (or Shift+Enter through them). VS Code
# opens a Python Interactive Window panel and renders the live plot
# directly inside it -- no separate window, no extra serial-specific
# VS Code extension needed.
#
# Reads the exact same space-separated `Label:value` lines
# theinterface.ino already prints for Arduino's own Serial Plotter --
# see `printChannel()` in theinterface.ino and its comment ("Field
# order/text matches the original hand-duplicated version exactly, so
# Serial Plotter label parsing is unaffected"). This script doesn't
# need the sketch to change at all, and deliberately doesn't touch it.
#
# Requires: pyserial, matplotlib, ipykernel (see tools/requirements.txt
# -- `pip install -r tools/requirements.txt`). VS Code also offers to
# install `ipykernel` automatically the first time you run a cell here
# if it's missing.

# %%
import re
import time
from collections import deque

import matplotlib.pyplot as plt
import serial
import serial.tools.list_ports

PORT = None              # e.g. "COM9" -- None auto-detects, see find_port() below
BAUD = 115200
FALLBACK_PORT = "COM9"   # this project's known port on the dev machine -- see the
                          # arduino-cli-connection memory
HISTORY = 200             # samples kept per channel (~8s at the sketch's 40ms print rate)

# Channels grouped by scale so they share a y-axis sensibly -- BPM
# (roughly 40-180), HRV (ms), SpO2 (roughly 70-100%), raw Wave
# (unbounded AC-coupled ADC counts), Motor (0-255 PWM duty). Wave and
# Motor get their own subplots since they'd otherwise swamp the others'
# scale. Beat/State/Mode are left out of the plot (they're flags/enums,
# not continuous signals) -- serial_monitor.py shows the full raw line
# including those, nothing is lost by omitting them here.
CHANNEL_GROUPS = [
    ("BPM", ["BPM1", "BPM2"]),
    ("HRV (ms)", ["HRV1", "HRV2"]),
    ("SpO2 (%)", ["SpO2_1", "SpO2_2"]),
    ("Wave (raw)", ["Wave1", "Wave2"]),
    ("Motor (PWM)", ["Motor1", "Motor2"]),
]
ALL_CHANNELS = [ch for _, chs in CHANNEL_GROUPS for ch in chs]

LINE_RE = re.compile(r"(\w+):(-?\d+(?:\.\d+)?)")


def find_port():
    """Best-effort auto-detect: the first port whose description looks
    like an Arduino, else FALLBACK_PORT. Override via PORT above if this
    picks the wrong thing, or you're on a different machine/session."""
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
    # See serial_monitor.py's open_port() -- same DTR/RTS requirement,
    # same reasoning (the arduino-cli-connection memory has the details).
    ser.dtr = True
    ser.rts = True
    ser.open()
    time.sleep(3)  # let setup() finish after the DTR-triggered reset
    return ser


def parse_line(line, buffers):
    for name, value in LINE_RE.findall(line):
        if name in buffers:
            try:
                buffers[name].append(float(value))
            except ValueError:
                pass


# %%
port = PORT or find_port()
print(f"Connecting to {port} @ {BAUD} baud...")
ser = open_port(port, BAUD)
print("Connected.")

buffers = {ch: deque(maxlen=HISTORY) for ch in ALL_CHANNELS}

fig, axes = plt.subplots(len(CHANNEL_GROUPS), 1, figsize=(9, 10), sharex=False)
fig.suptitle("The Interface — Live Serial Plot")
lines = {}
for ax, (title, channels) in zip(axes, CHANNEL_GROUPS):
    ax.set_ylabel(title)
    for ch in channels:
        (line,) = ax.plot([], [], label=ch)
        lines[ch] = line
    ax.legend(loc="upper right", fontsize=8)
fig.tight_layout()

# %%
# Live-updates the plot above until interrupted -- use the Interactive
# Window toolbar's "Interrupt Kernel" button (or Ctrl+C if you're
# running this file as a plain script in a terminal instead) to stop.
try:
    while True:
        raw = ser.readline().decode("utf-8", errors="replace").rstrip()
        if raw:
            parse_line(raw, buffers)
            for ch, buf in buffers.items():
                xs = range(len(buf))
                lines[ch].set_data(xs, buf)
            for ax in axes:
                ax.relim()
                ax.autoscale_view()
            fig.canvas.draw()
            plt.pause(0.001)
except KeyboardInterrupt:
    print("Stopped.")

# %%
ser.close()
print("Port closed.")
