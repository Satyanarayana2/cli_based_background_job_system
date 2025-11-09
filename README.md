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

*Installation*

# Clone the repository
git clone https://github.com/<your-username>/QueueCTL.git
cd QueueCTL

# Install dependencies
pip install -r requirements.txt

# Run CLI commands
python -m queuectl --help

*CLI Commands*

QueueCTL supports 11 CLI commands, grouped by category:

#

Category

Command

Description

1

Enqueue

queuectl enqueue '{"id":"job1","command":"sleep 2"}'

Add a new background job

2



queuectl enqueue --file scripts/task.py

Enqueue a job from a Python/Bash file

3

Workers

queuectl worker start --count 3

Start one or more worker processes

4



queuectl worker stop

Stop all running workers gracefully

5

Status

queuectl status

Display summary of job states & workers

6

List Jobs

queuectl list --state pending

List jobs filtered by state

7

DLQ

queuectl dlq list

View jobs in the Dead Letter Queue

8



queuectl dlq retry <job_id>

Retry a failed DLQ job

9

Config

queuectl config set max_retries 3

Update configuration values

10



queuectl config show

Display all configuration settings

11

Metrics

queuectl metrics

Show real-time system and worker stats

*Job Lifecycle*

State

Description

pending

Waiting to be picked up by a worker

processing

Currently being executed

completed

Successfully executed

failed

Failed but retryable

dead

Permanently failed (moved to DLQ)

*Retry & Backoff Mechanism*

Failed jobs are retried automatically with exponential backoff:



For example, with backoff_base = 2 and max_retries = 3:

1st retry → 2s delay
2nd retry → 4s delay
3rd retry → 8s delay

After exceeding max_retries, jobs move automatically to the Dead Letter Queue.

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

📊 QueueCTL System Metrics
-----------------------------------
🕐 Last Heartbeat : 2025-11-09T23:41:14
⏱️  Uptime (s)     : 126
✅ Jobs Completed : 12
❌ Failed Jobs    : 2
💠 DLQ Jobs       : 1
🧠 CPU Usage (%)  : 10.5
📦 Memory (MB)    : 46.72
-----------------------------------

*Testing Examples*

# Enqueue some jobs
queuectl enqueue '{"id":"job1","command":"echo hello"}'
queuectl enqueue --file scripts/task.py

# List pending jobs
queuectl list --state pending

# Start a worker
queuectl worker start --count 1

# View queue status
queuectl status

# Check metrics
queuectl metrics

# Retry failed jobs
queuectl dlq retry job1

*Known Limitations*

Metrics are global, not per-worker (shared file model)

No distributed or remote queue system (local-only)

Worker restart persistence handled at the job level, not the process pool




