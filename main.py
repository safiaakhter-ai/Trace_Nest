"""TraceNest: desktop tools for inspecting local operating-system activity."""

import queue
import tkinter as tk
from datetime import datetime
from tkinter import filedialog, messagebox, ttk

import psutil
from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

from database import get_alert_history, initialize_database, log_event
from export_alerts import export_alerts


CPU_ALERT_THRESHOLD = 85
RAM_ALERT_THRESHOLD = 90
MAX_TABLE_ROWS = 500


class TraceNestFileHandler(FileSystemEventHandler):
    def __init__(self, event_queue):
        super().__init__()
        self.event_queue = event_queue

    def on_created(self, event):
        if not event.is_directory:
            self.event_queue.put(("CREATED", event.src_path))

    def on_modified(self, event):
        if not event.is_directory:
            self.event_queue.put(("MODIFIED", event.src_path))

    def on_deleted(self, event):
        if not event.is_directory:
            self.event_queue.put(("DELETED", event.src_path))

    def on_moved(self, event):
        if not event.is_directory:
            self.event_queue.put(("MOVED", event.dest_path))


class TraceNestApp:
    def __init__(self, root):
        self.root = root
        self.root.title("TraceNest | Local Activity Monitor")
        self.root.geometry("1150x720")
        self.root.minsize(900, 600)
        self.root.configure(bg="#0b1120")

        self.bg = "#0b1120"
        self.panel = "#151e30"
        self.accent = "#38bdf8"
        self.text = "#e5e7eb"
        self.muted = "#94a3b8"

        self.process_data = []
        self.metrics = {}

        # One alert per continuous threshold breach; re-arm when it clears.
        self.alert_active = {
            "cpu": False,
            "ram": False,
        }
        initialize_database()
        self.setup_style()
        self.build_header()
        self.build_dashboard()
        self.build_tabs()
        self.auto_refresh_processes()
        self.update_metrics()
        self.check_alerts()

    def setup_style(self):
        style = ttk.Style()
        style.theme_use("clam")

        style.configure(
            "Treeview",
            background=self.panel,
            foreground=self.text,
            fieldbackground=self.panel,
            rowheight=30,
            borderwidth=0,
            font=("Segoe UI", 10)
        )

        style.configure(
            "Treeview.Heading",
            background="#243149",
            foreground=self.text,
            font=("Segoe UI", 10, "bold"),
            padding=8
        )

        style.map(
            "Treeview",
            background=[("selected", "#075985")],
            foreground=[("selected", "#ffffff")]
        )

        style.configure(
            "TNotebook",
            background=self.bg,
            borderwidth=0
        )

        style.configure(
            "TNotebook.Tab",
            background=self.panel,
            foreground=self.text,
            padding=(18, 10),
            font=("Segoe UI", 10)
        )

        style.map(
            "TNotebook.Tab",
            background=[("selected", "#075985")],
            foreground=[("selected", "#ffffff")]
        )

    def build_header(self):
        header = tk.Frame(self.root, bg=self.bg)
        header.pack(fill="x", padx=25, pady=(20, 12))

        title = tk.Label(
            header,
            text="TraceNest",
            font=("Segoe UI", 25, "bold"),
            fg=self.accent,
            bg=self.bg
        )
        title.pack(side="left")

        subtitle = tk.Label(
            header,
            text="Local Activity Monitor",
            font=("Segoe UI", 11),
            fg=self.muted,
            bg=self.bg
        )
        subtitle.pack(side="left", padx=15, pady=(10, 0))

        refresh_btn = tk.Button(
            header,
            text="Refresh Processes",
            command=self.refresh_processes,
            bg="#075985",
            fg="white",
            activebackground="#0369a1",
            activeforeground="white",
            relief="flat",
            padx=15,
            pady=9,
            cursor="hand2"
        )
        refresh_btn.pack(side="right")

    def build_dashboard(self):
        container = tk.Frame(self.root, bg=self.bg)
        container.pack(fill="x", padx=25, pady=8)

        cards = [
            ("Processes", "processes"),
            ("CPU Usage", "cpu"),
            ("RAM Usage", "ram"),
            ("System", "system")
        ]

        for title, key in cards:
            card = tk.Frame(
                container,
                bg=self.panel,
                padx=18,
                pady=14
            )
            card.pack(
                side="left",
                fill="both",
                expand=True,
                padx=(0, 10)
            )

            tk.Label(
                card,
                text=title,
                font=("Segoe UI", 10),
                fg=self.muted,
                bg=self.panel
            ).pack(anchor="w")

            value = tk.Label(
                card,
                text="Loading...",
                font=("Segoe UI", 20, "bold"),
                fg=self.accent,
                bg=self.panel
            )
            value.pack(anchor="w", pady=(8, 0))

            self.metrics[key] = value

    def build_tabs(self):
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(
            fill="both",
            expand=True,
            padx=25,
            pady=(12, 8)
        )

        self.overview_tab = tk.Frame(
            self.notebook, bg=self.bg
        )
        self.process_tab = tk.Frame(
            self.notebook, bg=self.bg
        )
        self.file_tab = tk.Frame(
            self.notebook, bg=self.bg
        )
        self.network_tab = tk.Frame(
            self.notebook, bg=self.bg
        )
        self.alert_tab = tk.Frame(
            self.notebook, bg=self.bg
        )

        self.notebook.add(
            self.overview_tab, text="Overview"
        )
        self.notebook.add(
            self.process_tab, text="Processes"
        )
        self.notebook.add(
            self.file_tab, text="File Activity"
        )
        self.notebook.add(
            self.network_tab, text="Network Ports"
        )
        self.notebook.add(
            self.alert_tab, text="Alerts"
        )

        self.build_overview()
        self.build_process_tab()
        self.build_file_tab()

        self.build_network_tab()
        self.build_alert_tab()

    def build_overview(self):
        tk.Label(
            self.overview_tab,
            text="System Overview",
            font=("Segoe UI", 19, "bold"),
            fg=self.text,
            bg=self.bg
        ).pack(anchor="w", padx=20, pady=(22, 8))

        tk.Label(
            self.overview_tab,
            text=(
                "TraceNest collects local system information "
                "to help investigate process and resource activity."
            ),
            font=("Segoe UI", 11),
            fg=self.muted,
            bg=self.bg,
            wraplength=850,
            justify="left"
        ).pack(anchor="w", padx=20, pady=5)

        self.clock_label = tk.Label(
            self.overview_tab,
            text="",
            font=("Segoe UI", 11),
            fg=self.accent,
            bg=self.bg
        )
        self.clock_label.pack(anchor="w", padx=20, pady=12)

        tk.Label(
            self.overview_tab,
            text="Available modules",
            font=("Segoe UI", 13, "bold"),
            fg=self.text,
            bg=self.bg
        ).pack(anchor="w", padx=20, pady=(15, 5))

        for item in [
            "Live process and resource monitoring",
            "File activity investigation",
            "Network listening port inspection",
            "Rule-based anomaly detection and reporting"
        ]:
            tk.Label(
                self.overview_tab,
                text=f"  •  {item}",
                font=("Segoe UI", 11),
                fg=self.muted,
                bg=self.bg
            ).pack(anchor="w", padx=25, pady=4)

    def build_process_tab(self):
        top = tk.Frame(self.process_tab, bg=self.bg)
        top.pack(fill="x", padx=12, pady=12)

        tk.Label(
            top,
            text="Running Processes",
            font=("Segoe UI", 16, "bold"),
            fg=self.text,
            bg=self.bg
        ).pack(side="left")

        self.search_var = tk.StringVar()

        search = tk.Entry(
            top,
            textvariable=self.search_var,
            bg=self.panel,
            fg=self.text,
            insertbackground="white",
            relief="flat",
            font=("Segoe UI", 11),
            width=25
        )
        search.pack(side="right", ipady=7)

        self.search_var.trace_add(
            "write",
            lambda *_: self.display_processes()
        )

        columns = (
            "pid", "name", "username",
            "cpu", "memory", "status"
        )

        self.process_tree = ttk.Treeview(
            self.process_tab,
            columns=columns,
            show="headings"
        )

        headings = {
            "pid": "PID",
            "name": "Process Name",
            "username": "User",
            "cpu": "CPU %",
            "memory": "Memory MB",
            "status": "Status"
        }

        widths = {
            "pid": 75,
            "name": 220,
            "username": 180,
            "cpu": 100,
            "memory": 120,
            "status": 120
        }

        for column in columns:
            self.process_tree.heading(
                column, text=headings[column]
            )
            self.process_tree.column(
                column,
                width=widths[column],
                minwidth=60
            )

        scrollbar = ttk.Scrollbar(
            self.process_tab,
            orient="vertical",
            command=self.process_tree.yview
        )

        self.process_tree.configure(
            yscrollcommand=scrollbar.set
        )

        self.process_tree.pack(
            side="left",
            fill="both",
            expand=True,
            padx=(12, 0),
            pady=(0, 12)
        )

        scrollbar.pack(
            side="right",
            fill="y",
            padx=(0, 12),
            pady=(0, 12)
        )


    def build_file_tab(self):
        self.selected_folder = None
        self.file_observer = None
        self.file_event_queue = queue.Queue()

        top = tk.Frame(self.file_tab, bg=self.bg)
        top.pack(fill="x", padx=15, pady=15)

        tk.Label(
            top,
            text="File Activity Monitor",
            font=("Segoe UI", 16, "bold"),
            fg=self.text,
            bg=self.bg
        ).pack(anchor="w", pady=(0, 10))

        self.folder_path_label = tk.Label(
            top,
            text="No folder selected",
            fg=self.muted,
            bg=self.bg,
            wraplength=850,
            justify="left"
        )
        self.folder_path_label.pack(anchor="w", pady=5)

        buttons = tk.Frame(top, bg=self.bg)
        buttons.pack(anchor="w", pady=8)

        tk.Button(
            buttons,
            text="Choose Folder",
            command=self.choose_monitor_folder,
            bg="#075985",
            fg="white",
            relief="flat",
            padx=12,
            pady=7
        ).pack(side="left", padx=(0, 8))

        tk.Button(
            buttons,
            text="Start Monitoring",
            command=self.start_file_monitor,
            bg="#166534",
            fg="white",
            relief="flat",
            padx=12,
            pady=7
        ).pack(side="left", padx=8)

        tk.Button(
            buttons,
            text="Stop Monitoring",
            command=self.stop_file_monitor,
            bg="#991b1b",
            fg="white",
            relief="flat",
            padx=12,
            pady=7
        ).pack(side="left", padx=8)

        self.file_status_label = tk.Label(
            top,
            text="Status: Not monitoring",
            fg=self.muted,
            bg=self.bg
        )
        self.file_status_label.pack(anchor="w", pady=5)

        columns = ("time", "event", "path")

        self.file_tree = ttk.Treeview(
            self.file_tab,
            columns=columns,
            show="headings"
        )

        self.file_tree.heading("time", text="Time")
        self.file_tree.heading("event", text="Event")
        self.file_tree.heading("path", text="File Path")

        self.file_tree.column("time", width=130)
        self.file_tree.column("event", width=120)
        self.file_tree.column("path", width=650)

        scrollbar = ttk.Scrollbar(
            self.file_tab,
            orient="vertical",
            command=self.file_tree.yview
        )

        self.file_tree.configure(
            yscrollcommand=scrollbar.set
        )

        self.file_tree.pack(
            side="left",
            fill="both",
            expand=True,
            padx=(12, 0),
            pady=(0, 12)
        )

        scrollbar.pack(
            side="right",
            fill="y",
            padx=(0, 12),
            pady=(0, 12)
        )

        self.root.after(300, self.poll_file_events)
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

    def choose_monitor_folder(self):
        if self.file_observer is not None:
            messagebox.showinfo(
                "Stop monitoring first",
                "Stop the current monitor before choosing another folder."
            )
            return

        folder = filedialog.askdirectory(
            title="Select a folder to monitor"
        )

        if folder:
            self.selected_folder = folder
            self.folder_path_label.config(text=folder)
            self.file_status_label.config(
                text="Status: Folder selected"
            )

    def start_file_monitor(self):
        if not self.selected_folder:
            messagebox.showwarning(
                "Select Folder",
                "Please choose a folder first."
            )
            return

        if self.file_observer is not None:
            return

        try:
            observer = Observer()

            observer.schedule(
                TraceNestFileHandler(self.file_event_queue),
                self.selected_folder,
                recursive=True
            )

            observer.start()
            self.file_observer = observer

            self.file_status_label.config(
                text="Status: Monitoring active"
            )

        except Exception as error:
            if "observer" in locals() and observer.is_alive():
                observer.stop()
                observer.join(timeout=2)
            messagebox.showerror(
                "Monitoring Error",
                str(error)
            )

    def stop_file_monitor(self):
        if self.file_observer is not None:
            self.file_observer.stop()
            self.file_observer.join(timeout=2)
            self.file_observer = None

        if hasattr(self, "file_status_label"):
            self.file_status_label.config(
                text="Status: Not monitoring"
            )

    def poll_file_events(self):
        try:
            while True:
                event_type, path = (
                    self.file_event_queue.get_nowait()
                )

                self.file_tree.insert(
                    "",
                    0,
                    values=(
                        datetime.now().strftime("%H:%M:%S"),
                        event_type,
                        path
                    )
                )

                items = self.file_tree.get_children()

                if len(items) > MAX_TABLE_ROWS:
                    self.file_tree.delete(items[-1])

        except queue.Empty:
            pass

        if self.root.winfo_exists():
            self.root.after(300, self.poll_file_events)

    def on_close(self):
        self.stop_file_monitor()
        self.root.destroy()


    def build_alert_tab(self):
        """Create the live, rule-based system alerts table."""
        top = tk.Frame(self.alert_tab, bg=self.bg)
        top.pack(fill="x", padx=15, pady=15)

        tk.Label(
            top,
            text="System Anomaly Alerts",
            font=("Segoe UI", 16, "bold"),
            fg=self.text,
            bg=self.bg
        ).pack(anchor="w")

        tk.Label(
            top,
            text=(f"Shows warnings at CPU {CPU_ALERT_THRESHOLD}%+ "
              f"and RAM {RAM_ALERT_THRESHOLD}%+ usage."),
            font=("Segoe UI", 10),
            fg=self.muted,
            bg=self.bg
        ).pack(anchor="w", pady=8)


        tk.Button(
            self.alert_tab,
            text="Refresh History",
            command=self.refresh_alert_history,
            bg="#075985",
            fg="white",
            relief="flat",
            padx=12,
            pady=7,
            cursor="hand2"
        ).pack(anchor="w", padx=15, pady=8)

        tk.Button(
            self.alert_tab,
            text="Export Alerts",
            command=export_alerts,
            bg="#075985",
            fg="white",
            relief="flat",
            padx=12,
            pady=7,
            cursor="hand2"
        ).pack(anchor="w", padx=15, pady=(0, 8))

        columns = ("time", "severity", "message")

        self.alert_tree = ttk.Treeview(
            self.alert_tab,
            columns=columns,
            show="headings"
        )


        self.alert_tree.heading("time", text="Time")
        self.alert_tree.heading("severity", text="Severity")
        self.alert_tree.heading("message", text="Alert Message")

        self.alert_tree.column("time", width=150, minwidth=90)
        self.alert_tree.column("severity", width=120, minwidth=90)
        self.alert_tree.column("message", width=650, minwidth=250)
        self.alert_tree.tag_configure("warning", foreground="#fbbf24")

        scrollbar = ttk.Scrollbar(
            self.alert_tab,
            orient="vertical",
            command=self.alert_tree.yview
        )
        self.alert_tree.configure(yscrollcommand=scrollbar.set)
        self.alert_tree.pack(
            side="left",
            fill="both",
            expand=True,
            padx=(15, 0),
            pady=(0, 15)
        )

        scrollbar.pack(
            side="right",
            fill="y",
            padx=(0, 15),
            pady=(0, 15)
        )

        self.refresh_alert_history()


    def refresh_alert_history(self):
        # Clear existing history
        for item in self.alert_tree.get_children():
            self.alert_tree.delete(item)

        # Load saved alerts from SQLite
        for timestamp, severity, message in get_alert_history():
            self.alert_tree.insert(
                "",
                "end",
                values=(timestamp, severity, message)
            )


    def check_alerts(self):
        """Check system resource thresholds every five seconds."""
        cpu = psutil.cpu_percent(interval=None)
        ram = psutil.virtual_memory().percent

        conditions = {
            "cpu": (cpu >= CPU_ALERT_THRESHOLD,
                    f"High CPU usage detected: {cpu:.1f}%"),
            "ram": (ram >= RAM_ALERT_THRESHOLD,
                    f"High memory usage detected: {ram:.1f}%"),
        }

        for alert_type, (triggered, message) in conditions.items():
            if triggered and not self.alert_active[alert_type]:
                self.alert_tree.insert(
                    "", 0,
                    values=(
                        datetime.now().strftime("%H:%M:%S"),
                        "WARNING",
                        message,
                    ),
                    tags=("warning",),
                )
                log_event(
                    category=alert_type.upper(),
                    severity="WARNING",
                    message=message
                )
                self.alert_active[alert_type] = True

                # Avoid letting the live table grow without limit.
                entries = self.alert_tree.get_children()
                if len(entries) > MAX_TABLE_ROWS:
                    self.alert_tree.delete(entries[-1])
            elif not triggered:
                self.alert_active[alert_type] = False

        self.root.after(5000, self.check_alerts)


    def build_network_tab(self):
        top = tk.Frame(self.network_tab, bg=self.bg)
        top.pack(fill="x", padx=15, pady=15)

        tk.Label(
            top,
            text="Network Ports Inspector",
            font=("Segoe UI", 16, "bold"),
            fg=self.text,
            bg=self.bg
        ).pack(side="left")

        tk.Button(
            top,
            text="Refresh Ports",
            command=self.refresh_network_ports,
            bg="#075985",
            fg="white",
            relief="flat",
            padx=12,
            pady=7
        ).pack(side="right")

        self.network_info_label = tk.Label(
            self.network_tab,
            text="Local network ports and connections mapped with process name and PID.",
            font=("Segoe UI", 10),
            fg=self.muted,
            bg=self.bg
        )
        self.network_info_label.pack(anchor="w", padx=15, pady=(0, 8))

        columns = ("protocol", "address", "port", "pid", "process", "status", "flag")

        self.network_tree = ttk.Treeview(
            self.network_tab,
            columns=columns,
            show="headings"
        )

        self.network_tree.heading("protocol", text="Protocol")
        self.network_tree.heading("address", text="Local Address")
        self.network_tree.heading("port", text="Port")
        self.network_tree.heading("pid", text="PID")
        self.network_tree.heading("process", text="Process Name")
        self.network_tree.heading("status", text="Status")
        self.network_tree.heading("flag", text="Flag")

        self.network_tree.column("protocol", width=90)
        self.network_tree.column("address", width=180)
        self.network_tree.column("port", width=80)
        self.network_tree.column("pid", width=80)
        self.network_tree.column("process", width=200)
        self.network_tree.column("status", width=120)
        self.network_tree.column("flag", width=140)

        scrollbar = ttk.Scrollbar(
            self.network_tab,
            orient="vertical",
            command=self.network_tree.yview
        )

        self.network_tree.configure(yscrollcommand=scrollbar.set)

        self.network_tree.pack(
            side="left",
            fill="both",
            expand=True,
            padx=(12, 0),
            pady=(0, 12)
        )

        scrollbar.pack(
            side="right",
            fill="y",
            padx=(0, 12),
            pady=(0, 12)
        )

        self.refresh_network_ports()

    def refresh_network_ports(self):
        if not hasattr(self, "network_tree"):
            return

        for item in self.network_tree.get_children():
            self.network_tree.delete(item)

        seen = set()

        try:
            connections = psutil.net_connections(kind="inet")
        except (psutil.Error, OSError) as exc:
            self.network_info_label.config(
                text=f"Could not inspect network connections: {exc}"
            )
            return

        self.network_info_label.config(
            text="Local connections (visibility may be limited without admin rights)."
        )

        for conn in connections:
            try:
                if not conn.laddr:
                    continue

                ip = conn.laddr.ip if hasattr(conn.laddr, "ip") else conn.laddr[0]
                port = conn.laddr.port if hasattr(conn.laddr, "port") else conn.laddr[1]
                pid = conn.pid if conn.pid is not None else "N/A"
                status = conn.status if conn.status else "N/A"

                if conn.type == 1:
                    protocol = "TCP"
                elif conn.type == 2:
                    protocol = "UDP"
                else:
                    protocol = "Other"

                process_name = "Unknown"
                if conn.pid:
                    try:
                        process_name = psutil.Process(conn.pid).name()
                    except Exception:
                        process_name = "AccessDenied"

                key = (protocol, ip, port, pid, process_name, status)
                if key in seen:
                    continue
                seen.add(key)

                # An all-interface bind does not necessarily mean the
                # port is accessible from the internet (firewalls still apply).
                if str(ip) in ("0.0.0.0", "::"):
                    flag = "All interfaces"
                elif isinstance(port, int) and port < 1024:
                    flag = "Low port"
                else:
                    flag = "Specific IP"

                self.network_tree.insert(
                    "",
                    "end",
                    values=(
                        protocol,
                        ip,
                        port,
                        pid,
                        process_name,
                        status,
                        flag
                    )
                )

            except Exception:
                continue
        
    def refresh_processes(self):
        self.process_data = []
        core_count = max(1, psutil.cpu_count(logical=True) or 1)

        for proc in psutil.process_iter(
            ["pid", "name", "username", "status", "memory_info"]
        ):
            try:
                info = proc.info
                memory = info.get("memory_info")

                # psutil's per-process CPU percentage can exceed 100% on
                # multicore systems. Normalize it for a dashboard-scale view.
                # PID 0 on Windows represents the idle process, not CPU load.
                raw_cpu = proc.cpu_percent(interval=None)
                cpu_percent = min(100.0, max(0.0, raw_cpu / core_count))
                if info.get("pid") == 0:
                    cpu_percent = 0.0

                self.process_data.append({
                    "pid": info.get("pid", ""),
                    "name": info.get("name") or "Unknown",
                    "username": info.get("username") or "N/A",
                    "cpu": cpu_percent,
                    "memory": (
                        memory.rss / (1024 * 1024)
                        if memory else 0
                    ),
                    "status": info.get("status") or "Unknown"
                })

            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue

        self.display_processes()

        self.metrics["processes"].config(
            text=str(len(self.process_data))
        )

    def auto_refresh_processes(self):
        """Keep a single automatic refresh loop, separate from manual refresh."""
        self.refresh_processes()
        self.root.after(3000, self.auto_refresh_processes)

    def display_processes(self):
        if not hasattr(self, "process_tree"):
            return

        for item in self.process_tree.get_children():
            self.process_tree.delete(item)

        query = self.search_var.get().strip().lower()

        for proc in self.process_data:
            if query and query not in (
                str(proc["pid"]) + " " + proc["name"]
            ).lower():
                continue

            self.process_tree.insert(
                "",
                "end",
                values=(
                    proc["pid"],
                    proc["name"],
                    proc["username"],
                    f'{proc["cpu"]:.1f}',
                    f'{proc["memory"]:.1f}',
                    proc["status"]
                )
            )

    def update_metrics(self):
        cpu = psutil.cpu_percent(interval=None)
        ram = psutil.virtual_memory().percent

        self.metrics["cpu"].config(text=f"{cpu:.1f}%")
        self.metrics["ram"].config(text=f"{ram:.1f}%")
        self.metrics["system"].config(text="Online")

        self.clock_label.config(
            text="Last dashboard update: "
            + datetime.now().strftime("%d %b %Y, %I:%M:%S %p")
        )

        self.root.after(2000, self.update_metrics)


if __name__ == "__main__":
    root = tk.Tk()
    app = TraceNestApp(root)
    root.mainloop()
