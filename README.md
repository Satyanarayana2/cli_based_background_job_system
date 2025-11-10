# cli_based_background_job_system
A CLI-based background job processor with retries, persistence, and worker management.

*Overview*

QueueCTL is a lightweight, production-grade job queue system built as part of the FLAM Backend Developer Internship Assignment.It provides a simple CLI interface to enqueue background jobs, process them using multiple workers, manage retries with exponential backoff, and handle permanently failed jobs using a Dead Letter Queue (DLQ).

All job data is persisted locally via SQLite and configurations are managed dynamically through JSON-based settings.

*Features*

Enqueue and manage background jobs (JSON or file-based)
Multiple worker processes
Retry mechanism with exponential backoff
Dead Letter Queue (DLQ) handling
Persistent job storage (SQLite)
Configurable system parameters (via CLI)
Real-time job metrics and system stats
Graceful shutdown for workers
Modular code structure with clean CLI interface

*Tech Stack*

Language: Python 3.10+

Libraries: click, sqlite3, multiprocessing, subprocess, psutil, json, time, signal

Storage: SQLite (persistent file data/queue.db)

CLI Framework: click

*Project Structure*

```
queuectl/
│
├── queuectl/
│   ├── __init__.py
│   ├── __main__.py
│   ├── cli.py             # Main CLI entrypoint (queuectl ...)
│   ├── db.py              # SQLite persistence layer
│   ├── worker.py          # Worker logic, retries, DLQ, metrics
│   ├── config.py          # Config manager (JSON)
│   ├── logger.py          # Logging setup for CLI and workers
│   ├── utils.py           # Helper utilities (timestamps, metrics)
│   └── models.py          # (optional) Job data structures
│
├── data/
│   ├── queue.db           # Persistent job database
│   ├── config.json        # Config values (max_retries, backoff_base, etc.)
│   ├── logs/
│   │   └── queuectl.log   # Log file for all CLI and worker operations
│   └── metrics.json       # Real-time system stats
│
└── README.md
```


*Installation*

# Clone the repository
[git clone https://github.com/<your-username>/QueueCTL.git](https://github.com/Satyanarayana2/cli_based_background_job_system/)
cd QueueCTL

# QueueCTL – Job Queue Management CLI

QueueCTL is a lightweight, file-based job queue system with support for background execution, retries, dead-letter queue (DLQ), and worker management.

---

## CLI Commands

QueueCTL supports **11 commands**, organized by category:

| # | Category       | Command                                             | Description                                |
|---|----------------|-----------------------------------------------------|--------------------------------------------|
| 1 | **Enqueue**    | `queuectl enqueue '{"id":"job1","command":"sleep 2"}'` | Add a new background job                   |
| 2 |                | `queuectl enqueue --file scripts/task.py`           | Enqueue a job from a Python/Bash file      |
| 3 | **Workers**    | `queuectl worker start --count 3`                   | Start one or more worker processes         |
| 4 |                | `queuectl worker stop`                              | Stop all running workers gracefully        |
| 5 | **Status**     | `queuectl status`                                   | Display summary of job states & workers    |
| 6 | **List Jobs**  | `queuectl list --state pending`                     | List jobs filtered by state                |
| 7 | **DLQ**        | `queuectl dlq list`                                 | View jobs in the Dead Letter Queue         |
| 8 |                | `queuectl dlq retry <job_id>`                       | Retry a failed DLQ job                     |
| 9 | **Config**     | `queuectl config set max_retries 3`                 | Update configuration values                |
|10 |                | `queuectl config show`                              | Display all configuration settings         |
|11 | **Metrics**    | `queuectl metrics`                                  | Show real-time system and worker stats     |

---

## Job Lifecycle

| State        | Description                                      |
|--------------|--------------------------------------------------|
| `pending`    | Waiting to be picked up by a worker              |
| `processing` | Currently being executed                         |
| `completed`  | Successfully executed                            |
| `failed`     | Failed but retryable                             |
| `dead`       | Permanently failed (moved to DLQ)                |

---

## Retry & Backoff Mechanism

Failed jobs are **automatically retried** with **exponential backoff**.

### Example: `backoff_base = 2`, `max_retries = 3`

| Attempt | Delay Before Retry |
|---------|--------------------|
| 1st     | 2 seconds          |
| 2nd     | 4 seconds          |
| 3rd     | 8 seconds          |

> After exceeding `max_retries`, the job is moved to the **Dead Letter Queue (DLQ)**.



*Configuration*

The configuration is stored in data/config.json and can be managed via CLI.

Default values:

{
  "max_retries": 3,
  "backoff_base": 2,
  "log_level": "INFO",
  "worker_poll_interval": 1
}

Update configuration anytime:

queuectl config set max_retries 5
queuectl config show

*Metrics & Monitoring*

QueueCTL tracks system metrics live in data/metrics.json.

queuectl metrics

Example output:
```
 QueueCTL System Metrics
-----------------------------------
 Last Heartbeat : 2025-11-09T23:41:14
 Uptime (s)     : 126
 Jobs Completed : 12
 Failed Jobs    : 2
 DLQ Jobs       : 1
 CPU Usage (%)  : 10.5
 Memory (MB)    : 46.72
-----------------------------------
```

*Testing Examples*
## Live Testing Session (13 Jobs)

<details>
<summary><strong>Click to expand: Full end-to-end execution with retries, DLQ, and metrics</strong></summary>

```powershell
PS D:\FLAM Task> python -m queuectl reset
2025-11-10 13:37:25,397 [INFO] QueueCTL initialized.
QueueCTL initialized successfully.
Warning: This will delete all jobs and reset metrics. Continue? [y/N]: y
Jobs cleared and metrics reset successfully.

PS D:\FLAM Task> python -m queuectl metrics
2025-11-10 13:37:33,711 [INFO] QueueCTL initialized.
QueueCTL initialized successfully.
QueueCTL System Metrics
-----------------------------------
Last Heartbeat : None
Uptime (s) : 0
Jobs Completed : 0
Failed Jobs : 0
DLQ Jobs : 0
CPU Usage (%) : 0.0
Memory (MB) : 0.0
-----------------------------------

PS D:\FLAM Task> python .\bulk_enqueue.py
Found 13 jobs in jobs.json
Enqueued job1 -> echo Hello from QueueCTL!
Enqueued job2 -> python -c "print('Running quick inline Python job')"
Enqueued job3 -> python -c "import time; time.sleep(3); print('Simulated 3-sec job done')"
Enqueued job4 -> exit 1
Enqueued job5 -> python -c "print('Data pipeline executed successfully')"
Enqueued job6 -> python -c "import random; import sys; sys.exit(random.choice([0,1]))"
Enqueued job7 -> powershell -Command "Write-Host 'Running PowerShell style command'"
Enqueued job8 -> python -c "print('ML model inference simulation complete')"
Enqueued job9 -> python -c "import sys; sys.exit(1)"
Enqueued job10 -> python -c "raise Exception('Simulated crash for testing DLQ')"
Enqueued job11 -> python -c "open('non_existing_file.txt')"
Enqueued job12 -> python -c "import math; exit(99)"
Enqueued job13 -> invalid_command_that_does_not_exist
All jobs added to queue successfully!

PS D:\FLAM Task> python -m queuectl worker start --count 2
2025-11-10 13:37:53,699 [INFO] QueueCTL initialized.
QueueCTL initialized successfully.
2025-11-10 13:37:53,706 [INFO] Starting 2 worker(s)...
2025-11-10 13:37:53,707 [INFO] Starting 2 worker(s)...
WARNING:root:[W2] Job job4 failed with code 1.
WARNING:root:[W2] Job job4 failed with code 1.
WARNING:root:[W1] Job job6 failed with code 1.
WARNING:root:[W1] Job job6 failed with code 1.
WARNING:root:[W2] Job job4 failed with code 1.
ERROR:root:[W2] Job job4 moved to Dead Letter Queue after 3 retries.
WARNING:root:[W2] You can inspect this job with: queuectl dlq list
WARNING:root:[W2] Job job9 failed with code 1.
WARNING:root:[W2] Job job9 failed with code 1.
WARNING:root:[W1] Job job10 failed with code 1.
WARNING:root:[W1] Job job10 failed with code 1.
WARNING:root:[W2] Job job9 failed with code 1.
ERROR:root:[W2] Job job9 moved to Dead Letter Queue after 3 retries.
WARNING:root:[W2] You can inspect this job with: queuectl dlq list
WARNING:root:[W2] Job job11 failed with code 1.
WARNING:root:[W2] Job job11 failed with code 1.
WARNING:root:[W1] Job job10 failed with code 1.
ERROR:root:[W1] Job job10 moved to Dead Letter Queue after 3 retries.
WARNING:root:[W1] You can inspect this job with: queuectl dlq list
WARNING:root:[W1] Job job12 failed with code 99.
WARNING:root:[W1] Job job12 failed with code 99.
WARNING:root:[W2] Job job11 failed with code 1.
ERROR:root:[W2] Job job11 moved to Dead Letter Queue after 3 retries.
WARNING:root:[W2] You can inspect this job with: queuectl dlq list
WARNING:root:[W2] Job job13 failed with code 1.
WARNING:root:[W2] Job job13 failed with code 1.
WARNING:root:[W1] Job job12 failed with code 99.
ERROR:root:[W1] Job job12 moved to Dead Letter Queue after 3 retries.
WARNING:root:[W1] You can inspect this job with: queuectl dlq list
WARNING:root:[W2] Job job13 failed with code 1.
ERROR:root:[W2] Job job13 moved to Dead Letter Queue after 3 retries.
WARNING:root:[W2] You can inspect this job with: queuectl dlq list
WARNING:root:[W2] KeyboardInterrupt received. Exiting worker loop...
WARNING:root:[W1] KeyboardInterrupt received. Exiting worker loop...
2025-11-10 13:38:36,495 [WARNING] Received stop signal. Shutting down workers ...

PS D:\FLAM Task> python -m queuectl metrics
2025-11-10 13:38:45,145 [INFO] QueueCTL initialized.
QueueCTL initialized successfully.
QueueCTL System Metrics
-----------------------------------
Last Heartbeat : 2025-11-10T13:38:35+05:30
Uptime (s) : 42
Jobs Completed : 7
Failed Jobs : 0
DLQ Jobs : 6
CPU Usage (%) : 5.1
Memory (MB) : 23.4
-----------------------------------

PS D:\FLAM Task> python -m queuectl --help
Usage: python -m queuectl [OPTIONS] COMMAND [ARGS]...
  QueueCTL - Background Job Queue CLI
Options:
  --help Show this message and exit.
Commands:
  config Manage configuration settings.
  dlq Manage Dead Letter Queue (DLQ) jobs.
  enqueue Add a new job to the queue.
  list List jobs in the queue by state.
  metrics Display live worker and system metrics.
  reset Clear all jobs and metrics (keeps config and logs).
  status Show summary of all job states & active workers.
  worker Manage worker processes.

PS D:\FLAM Task> python -m queuectl dlq
2025-11-10 13:39:40,318 [INFO] QueueCTL initialized.
QueueCTL initialized successfully.
Usage: python -m queuectl dlq [OPTIONS] COMMAND [ARGS]...
  Manage Dead Letter Queue (DLQ) jobs.
Options:
  --help Show this message and exit.
Commands:
  list View jobs in the Dead Letter Queue.
  retry Retry a job from the DLQ by job ID.

PS D:\FLAM Task> python -m queuectl dlq list
2025-11-10 13:40:29,996 [INFO] QueueCTL initialized.
QueueCTL initialized successfully.
Dead Letter Queue:
- job4 | attempts=3 | command=exit 1
- job9 | attempts=3 | command=python -c "import sys; sys.exit(1)"
- job10 | attempts=3 | command=python -c "raise Exception('Simulated crash for testing DLQ')"
- job11 | attempts=3 | command=python -c "open('non_existing_file.txt')"
- job12 | attempts=3 | command=python -c "import math; exit(99)"
- job13 | attempts=3 | command=invalid_command_that_does_not_exist
Total Dead Jobs: 6

PS D:\FLAM Task> python -m queuectl dlq retry
2025-11-10 13:40:36,292 [INFO] QueueCTL initialized.
QueueCTL initialized successfully.
Usage: python -m queuectl dlq retry [OPTIONS] JOB_ID
Try 'python -m queuectl dlq retry --help' for help.
Error: Missing argument 'JOB_ID'.
PS D:\FLAM Task>





