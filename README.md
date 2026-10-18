# TraceNest — Local System Activity Monitor

**A Python-Based Desktop Application for System Monitoring, File Activity Tracking, Network Inspection, and Rule-Based Anomaly Detection.**

## Project Overview

TraceNest is a lightweight desktop application developed using Python to monitor and inspect local computer activities through a centralized graphical user interface.

The application provides information about CPU and RAM utilization, running processes, filesystem changes, and network connections. It also implements a rule-based alert mechanism to identify unusually high system resource usage.

TraceNest is designed to demonstrate practical concepts of operating system monitoring, event-driven programming, graphical user interfaces, and local database management.

## Key Features

### 1. System Resource Monitoring
- Monitor CPU utilization.
- Track RAM usage.
- Display the number of running processes.
- Automatically refresh system information.

### 2. Process Monitoring
- Display active processes.
- View Process ID (PID), process name, and status.
- Monitor process CPU and memory consumption.
- Search processes by name or PID.

### 3. File Activity Monitoring
- Monitor a user-selected directory.
- Detect file creation, modification, deletion, and movement.
- Display filesystem events in the application.
- Start and stop monitoring using interactive controls.

### 4. Network Port Inspection
- Inspect local TCP and UDP connections.
- Display IP addresses and port numbers.
- Identify associated processes when permissions allow.
- View connection status and descriptive port flags.

### 5. Rule-Based Anomaly Detection
- Detect high CPU usage at 85% or above.
- Detect high RAM usage at 90% or above.
- Generate warning messages.
- Prevent repeated alerts during continuous threshold violations.

### 6. Alert History and Reporting
- Store resource alerts in an SQLite database.
- View previous warning records.
- Refresh alert history.
- Export saved alerts into CSV format.

## Technologies Used

| Technology | Purpose |
|---|---|
| Python | Application development |
| Tkinter | Desktop graphical interface |
| psutil | System and process monitoring |
| Watchdog | Filesystem event monitoring |
| SQLite | Local alert storage |
| CSV | Alert report export |
| Queue | Thread-safe event communication |
| PyInstaller | Optional Windows executable packaging |

## System Architecture

TraceNest follows a modular application design consisting of the following components:

**Presentation Layer:** Tkinter provides the graphical interface and user interaction.

**Data Collection Layer:** psutil retrieves system metrics, process information, and network connections.

**File Monitoring Layer:** Watchdog observes filesystem changes and transfers events through a thread-safe queue.

**Detection Layer:** A rule-based mechanism evaluates CPU and RAM utilization against predefined thresholds.

**Storage and Reporting Layer:** SQLite stores resource alerts, while the CSV module supports exporting alert history.

**Basic Data Flow:**

Operating System → psutil / Watchdog → Python Application Logic → Tkinter GUI

For resource alerts:

System Metrics → Threshold Evaluation → SQLite Database → Alert History → CSV Export

## Project Structure

- `main.py` — Main application, GUI, and monitoring logic.
- `database.py` — SQLite database operations.
- `export_alerts.py` — CSV report generation.
- `requirements.txt` — Required Python packages.
- `Run_TraceNest.bat` — Windows application launcher.
- `Build_EXE_Windows.bat` — Windows executable build script.
- `tests/test_storage.py` — Storage and export tests.
- `ARCHITECTURE_AND_TESTING.txt` — Architecture and testing documentation.
- `README_START_HERE.txt` — Additional setup instructions.

## Installation and Setup

### Prerequisites

- Windows 10 or Windows 11
- Python 3 installed
- pip package manager

### Step 1: Clone the Repository

`git clone https://github.com/safiaakhter-ai/Trace_Nest.git`

### Step 2: Open the Project Directory

`cd Trace_Nest`

Navigate to the folder containing `main.py` and `requirements.txt` if the files are inside a subfolder.

### Step 3: Install Dependencies

`py -m pip install -r requirements.txt`

### Step 4: Run the Application

`py main.py`

Alternatively, Windows users can launch the application using `Run_TraceNest.bat`.

## How to Use

**Overview:** View CPU utilization, RAM usage, running process count, and system information.

**Processes:** Inspect running processes and search for specific applications.

**File Activity:** Select a folder, start monitoring, and observe filesystem events.

**Network Ports:** Refresh the connection list to inspect local network sockets and associated processes.

**Alerts:** Review saved CPU/RAM warnings and export alert history in CSV format.

## Testing

The project includes automated tests for database storage and CSV export operations.

To run the tests, use:

`py -m unittest discover -s tests -v`

Additional manual testing can be performed through the graphical interface.

## Current Limitations

- CPU and RAM alert thresholds are predefined.
- File activity events are displayed but are not persistently stored.
- Network inspection does not include packet-level analysis.
- The application monitors the local computer only.
- The anomaly detection mechanism is rule-based and does not use a trained machine learning model.
- Some system information may require additional operating system permissions.

## Future Improvements

- User-configurable resource thresholds.
- Persistent filesystem activity logs.
- Advanced resource visualization.
- Statistical and machine learning-based anomaly detection.
- Extended reporting capabilities.
- Improved background monitoring performance.
- Additional automated testing.

## Conclusion

TraceNest demonstrates the integration of system monitoring, filesystem event handling, network inspection, graphical interface development, and database management within a Python desktop application.

The project provides a foundation for further exploration of operating system utilities, monitoring tools, and event-driven software architecture.
