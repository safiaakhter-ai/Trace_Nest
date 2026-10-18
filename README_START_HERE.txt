TRACENEST - LOCAL SYSTEM ACTIVITY MONITOR
========================================

WHAT THIS PROJECT DOES
TraceNest is a Python desktop application for viewing running processes,
CPU and RAM usage, local file changes, network connection details, and
resource-usage warnings. It runs locally on your computer. This project uses
fixed rules for alerts; it does not contain a machine-learning model.

REQUIREMENTS
- Windows 10 or 11, with Python 3 installed (Python 3.10+ recommended)
- Tkinter (normally included with the standard Windows Python installer)
- Third-party packages listed in requirements.txt: psutil and watchdog
- Internet access may be needed only to install the packages on first run

HOW TO RUN
1. Right-click TraceNest_Test.zip and select Extract All.
2. Open the extracted TraceNest_Test folder.
3. Double-click Run_TraceNest.bat.
4. If Python is installed but the launcher cannot find it, check that
   the Python launcher (py) or Python (python) is on PATH.
5. Keep main.py, database.py, export_alerts.py and requirements.txt together.

ALTERNATIVE: RUN FROM THE TERMINAL
Open a terminal in this folder and enter:
    py -3 -m pip install -r requirements.txt
    py -3 main.py

MAIN FEATURES AND HOW TO VERIFY THEM
1. Overview: shows current overall CPU usage, RAM usage, process count
   and the last update time.
2. Processes: lists running processes. Search by PID or process name;
   click Refresh Processes to refresh manually.
3. File Activity: click Choose Folder, then Start Monitoring. Create,
   edit, rename, or delete a file in that folder and inspect the list.
   Click Stop Monitoring before choosing a different folder.
4. Network Ports: click Refresh Ports to see local network connections.
   Some process names and connections may be unavailable without
   administrator rights. "All interfaces" means bound to 0.0.0.0 or ::;
   it does not prove the port is reachable from the internet.
5. Alerts: CPU usage of at least 85% or RAM usage of at least 90%
   triggers a warning while the condition is present. An alert is logged
   only when that threshold is crossed, not on every refresh. Once the
   usage falls below the threshold, the same warning can be triggered
   on a later crossing. Use Refresh History to read stored alerts and
   Export Alerts to save the history as CSV.

FILES
- main.py: Tkinter GUI and monitoring logic
- database.py: local SQLite alert-history storage
- export_alerts.py: CSV export
- requirements.txt: third-party dependencies
- Run_TraceNest.bat: Windows run launcher
- Build_EXE_Windows.bat: optional executable build script
- tests/test_storage.py: automated tests for saving/loading alerts and CSV

DATA AND LIMITATIONS
- In normal Python mode, alert history is stored in tracenest.db in
  the project folder; the database is created on first run.
- In a bundled Windows executable, the database is stored under
  %LOCALAPPDATA%\TraceNest\tracenest.db.
- The application monitors only a folder the user explicitly selects.
- It does not send data to the cloud, scan other devices, or block
  suspicious processes or connections.
- Individual process CPU readings are normalized by the logical CPU
  count; the first per-process sample may display 0 until refresh.
- Resource alerts are rule-based warnings, not proof of malicious activity.

OPTIONAL: BUILD A WINDOWS EXE
Double-click Build_EXE_Windows.bat on a Windows computer where Python is
installed. The script installs PyInstaller if necessary and creates
    dist\TraceNest.exe
An EXE is not included in this ZIP, and Windows EXE builds have to be
validated on Windows.

AUTOMATED TESTS
From the project folder, run:
    py -3 -m unittest discover -s tests -v
These tests check alert-history storage and CSV export. GUI, filesystem
watching and process/port display also require manual testing on Windows.
