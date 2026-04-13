# Loom C2 — Feature Reference

> Enterprise-grade Command & Control / Remote Management platform.
> Built on Django + ASGI (Daphne/Channels) with a WebSocket-native architecture.

---

## 🖥️ Server (`/server`)

### Authentication & Access Control
- **Zero-Trust Login Portal** — All dashboard routes require authentication. Unauthenticated requests are redirected to a custom login page.
- **Self-Registration Disabled** — Operators cannot self-register. All user accounts must be provisioned directly by the root admin at `/admin/`.
- **Django Admin Panel** — Bespoke Glassmorphic dark-mode CSS override for a premium enterprise aesthetic (Inter font, neon gradients, glass-blur panels).

### Dashboard Overview (`/`)
- Live stat cards: Total Registered Nodes, Active (Online) Nodes, Offline Nodes, Total Tasks Executed, Completed Tasks.
- All values queried in real time from the core SQLite database on each page load.

### Registered Nodes & Telemetry (`/clients/`)
- Live table of all registered agents with: **Agent Identity**, **Network Footprint** (IP + MAC), **Hardware/OS Spec** (CPU%, RAM, Disk), **Status**, and **Last Ping** timestamp.
- **Client-side search bar** — Filter visible rows instantly by name, OS, or IP string.
- **🛑 Terminate Button** — Per-row remote kill-switch. Fires a `loom_kill_switch` instruction over the active WebSocket connection to shut down the remote agent process immediately.
- **🗑️ Purge Idle Nodes Button** — Bulk-deletes all clients with `offline` status from the database in one click, with confirmation prompt.

### Task Deployment (`/tasks/`)
- **Multi-Target Job Dispatch** — Select one or multiple agents simultaneously (CTRL/CMD+click) and deploy any system command in a single batch.
- **Vault Script Execution** — Select a pre-uploaded script from the File Vault and deploy it as a batch job using `loom_run_script <id>`.
- **Job Batch Progression** — Progress bar table tracking completion percentage per batch (completed tasks / total tasks).
- **Sub-Task Execution History** — Clickable rows for individual task records; clicking populates the Live Output Preview.
- **Live Output Preview (`<pre>` block)** — Displays raw stdout streamed from the agent over WebSockets. Falls back to cached historical output for completed tasks. Auto-scrolls to latest line.
- **Real-Time WebSocket Dispatch** — Tasks are pushed to the target agent immediately over the persistent ASGI channel without HTTP polling.

### Visual Node Explorer (`/explorer/`)
- **Remote Filesystem Navigation** — GUI-driven directory browser. Operators enter a path or click to traverse folders on the remote agent just like a file manager.
- **File Download** — Pulls any file from the remote agent's filesystem directly into the server's File Vault.
- **Payload Upload/Injection** — Upload a local file via the browser; the server stores it in the Vault and pushes it to a specified path on the remote agent over WebSockets.

### File Vault (`/vault/`)
- Secure file storage attached to the Django server. Stores scripts, payloads, and binary artifacts.
- Scripts can be referenced by ID for remote vault-execution via `loom_run_script <id>`.
- Files uploaded via the Node Explorer are automatically vaulted and assigned unique IDs.

### Execution Logs (`/logs/`)
- Persistent log table showing: **Agent Name**, **Task ID**, **STDOUT Stream** (rendered in a styled code block), **STDERR Exception**, and **Timestamp**.
- Populated automatically when the agent submits final output via the REST result API.

### REST API Endpoints
| Endpoint | Method | Description |
|---|---|---|
| `/api/register/` | POST | Agent self-registration and token issuance |
| `/api/heartbeat/` | POST | Agent telemetry ping (CPU, RAM, Disk, status) |
| `/api/submit-result/` | POST | Agent posts final task output and error |
| `/api/task/<id>/` | GET | Poll task status and cached output |
| `/api/script/<id>/download/` | GET | Download a vault script by ID |
| `/api/upload-file/` | POST | Agent uploads a file back to the vault |
| `/api/client/<id>/terminate/` | POST | Broadcast kill-switch to a specific agent |
| `/api/clients/purge/` | POST | Delete all offline clients from the database |

### WebSocket Consumers
- **`AgentConsumer`** (`/ws/agent/<token>/`) — Persistent bidirectional pipe between server and each remote agent. Handles task dispatch (`execute_task`), stdin piping (`agent_input`), and live stdout ingestion.
- **`TerminalConsumer`** (`/ws/terminal/<task_id>/`) — Bridges stdout chunks from the agent to the browser's Live Output Preview in real time.

### Exception Handling
- All REST API views are wrapped in `try/except Exception` blocks returning structured `{"error": "..."}` JSON responses with appropriate HTTP status codes (400/404/500).
- All WebSocket consumer handlers (`receive`, `terminal_output`, `execute_task`, `agent_input`) are individually wrapped to prevent a single bad message from crashing the WebSocket session.

---

## 🤖 Agent (`/client/agent.py`)

### Registration & Telemetry
- **Auto-Registration** — On startup, the agent collects hostname, OS version, CPU%, RAM, Disk usage, and MAC address, then POSTs to `/api/register/` to receive a unique token.
- **Heartbeat Thread** — A background daemon thread sends updated telemetry to `/api/heartbeat/` every 5 seconds, keeping the server dashboard live.

### WebSocket Connection
- Connects persistently to `ws://<server>/ws/agent/<token>/`.
- **Auto-Reconnect Loop** — If the WebSocket closes for any reason, the agent sleeps 5 seconds and reconnects automatically, ensuring persistent availability.

### Command Execution Engine
- **Shell Command Streaming** — Uses `subprocess.Popen` with unbuffered line-by-line stdout iteration, streaming each output line back over the WebSocket in real time as it is produced.
- **Stdin Piping** — Supports interactive stdin injection from the server (`loom_input` action), enabling interactive sessions with prompts.

### Built-in Loom Protocol Commands
| Command | Description |
|---|---|
| `loom_run_script <id>` | Downloads a script from the Vault by ID, saves to a temp directory, executes it, streams output, and **auto-deletes** the script file after completion — leaving no forensic trace. |
| `loom_fs_list <path>` | Returns a JSON directory listing of the specified path for the Node Explorer. |
| `loom_fs_download <path>` | Reads a file at the given path and uploads it back to the server Vault. |
| `loom_fs_upload <id> <dest>` | Downloads a Vault file by ID and drops it at the specified absolute path on the local filesystem. |
| `loom_kill_switch` | Sends a final acknowledgement message to the server, then calls `os._exit(0)` to immediately terminate the entire agent process. |

### Cross-Platform Persistence (`install_persistence()`)
Automatically installs a system-level startup entry on first run based on the detected OS:

| Platform | Method |
|---|---|
| **Windows** | Writes a `HKCU\...\Run` registry key pointing to the agent executable. |
| **Linux** | Appends a `@reboot nohup python3 <path>` entry to the user's `crontab`. |
| **macOS** | Creates a `LaunchAgent` plist at `~/Library/LaunchAgents/com.loom.agent.plist`. |

---

## 🗄️ Data Models

| Model | App | Key Fields |
|---|---|---|
| `Client` | `clients` | `id`, `name`, `token`, `ip_address`, `mac_address`, `os_version`, `cpu`, `ram`, `disk`, `status`, `last_seen` |
| `Task` | `tasks` | `id`, `batch`, `target_client`, `command`, `status`, `created_at` |
| `JobBatch` | `tasks` | `id`, `name`, `created_at` |
| `Log` | `logs` | `task`, `output`, `error`, `executed_at` |
| `ScriptFile` | `files` | `id`, `name`, `file`, `uploaded_at` |
