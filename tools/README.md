# Serial monitor & plotter (VS Code)

Two small scripts for watching `theinterface.ino`'s live serial output
without leaving VS Code. Neither changes the sketch — both just read
the same `Label:value` lines `printChannel()` already emits for
Arduino's own Serial Plotter (see the comment there: "Field order/text
matches the original hand-duplicated version exactly, so Serial
Plotter label parsing is unaffected").

## Setup

```bash
pip install -r tools/requirements.txt
```

## Serial monitor — plain text, in the integrated terminal

```bash
python tools/serial_monitor.py
```

Prints every line with a wall-clock timestamp. Open a VS Code terminal
(`` Ctrl+` ``) and run it there — that terminal panel *is* the monitor.

## Serial plotter — live graph, in the Interactive Window

Open `tools/serial_plotter.py` in VS Code, then run each `# %%` cell
in order (Shift+Enter, or the "Run Cell" code-lens above each cell).
VS Code opens a Python Interactive Window panel and renders the live
plot directly inside it. Requires the Python extension
(`ms-python.python`, recommended automatically for this workspace —
see `.vscode/extensions.json`) and `ipykernel`; VS Code offers to
install `ipykernel` automatically the first time you run a cell if
it's missing.

Five subplots, grouped by scale so each stays readable: BPM, HRV,
SpO2, raw Wave, and Motor PWM, each showing both participants. `Beat`/
`State`/`Mode` aren't plotted (they're flags/enums, not continuous
signals) — the monitor script above shows the full raw line including
those, so nothing is lost by leaving them out of the graph.

To stop a running plot cell, use the Interactive Window toolbar's
"Interrupt Kernel" button.

## Port

Both scripts auto-detect the serial port (looks for a device whose
description mentions "Arduino" or "USB Serial"), falling back to COM9
if nothing matches (this project's known port on the dev machine — see
the `arduino-cli-connection` memory). Override with `--port COM7`
(monitor) or by setting `PORT = "COM7"` near the top of the plotter
script if auto-detect picks the wrong thing, or you're on a different
machine/session — COM assignments aren't stable across
reboots/replugs.

## Why DTR/RTS matter

The R4 Minima's native-USB serial silently produces no output unless
DTR/RTS are asserted on open — both scripts do this for you already.
If you adapt this code elsewhere, don't drop that, or reads will time
out looking exactly like a dead connection rather than an obvious
error.

## Alternative: a dedicated VS Code serial extension

If you'd rather use a GUI extension instead of these scripts, several
exist (e.g. `badlogicgames.serial-plotter`) — but they generally expect
their own line format (`>label:value,label:value\r\n`, with a leading
`>` and commas), which doesn't match what `printChannel()` emits today.
Since that output format is deliberately kept stable for compatibility
with Arduino's own Serial Plotter (per the comment in
`theinterface.ino`), these two scripts read the sketch's real,
unmodified output instead of asking the sketch to change to fit a
third-party extension.
