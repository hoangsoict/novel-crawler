# Coding Rules

## Tkinter & GUI Guidelines

1. **Integer Font Sizes Only**:
   - ALWAYS use integer values for font sizes in Tkinter widgets (`tk.Label`, `tk.Entry`, `tk.Button`, etc.) and `ttk.Style` font tuple configurations (e.g., `("Segoe UI", 10)` or `("Segoe UI", 9, "bold")`).
   - NEVER use floating-point font sizes like `9.5` or `10.5` because Tcl/Tkinter on Windows will fail at runtime with `_tkinter.TclError: expected integer but got "9.5"`.

2. **Windows High-DPI Awareness**:
   - Always include Windows High-DPI Awareness initialization via `ctypes.windll.shcore.SetProcessDpiAwareness(1)` at the start of GUI modules to ensure crisp rendering on high-resolution displays.

3. **Pre-build Pre-flight Check**:
   - Always run `python build_exe.py` preflight check before compiling executables.
