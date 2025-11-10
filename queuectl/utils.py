# queuectl/utils.py
from datetime import datetime
from zoneinfo import ZoneInfo
import time, os, json, psutil
from multiprocessing import Lock

# Timezone
IST = ZoneInfo("Asia/Kolkata")

# Paths
METRICS_PATH = "data/metrics.json"
_metrics_lock = Lock()

def now():
    """Return current time in IST as ISO8601 with offset."""
    return datetime.now(IST).isoformat(timespec="seconds")

def update_metrics(**kwargs):
    """Safely update metrics.json across multiple worker processes."""
    os.makedirs("data", exist_ok=True)
    _metrics_lock.acquire()
    try:
        # Load metrics safely
        metrics = {}
        if os.path.exists(METRICS_PATH):
            with open(METRICS_PATH, "r") as f:
                try:
                    metrics = json.load(f)
                except json.JSONDecodeError:
                    # Handle file corruption gracefully
                    metrics = {}
        
        # Merge new data and timestamp
        metrics.update(kwargs)
        metrics["last_updated"] = now()

        # Write back atomically
        with open(METRICS_PATH, "w") as f:
            json.dump(metrics, f, indent=4)

    finally:
        _metrics_lock.release()

def get_resource_usage():
    """Return current CPU and memory usage stats."""
    process = psutil.Process(os.getpid())
    return {
        "cpu_usage": psutil.cpu_percent(interval=0.1),
        "memory_usage": round(process.memory_info().rss / (1024 * 1024), 2)
    }


def now_utc():
    """Return UTC time as ISO string."""
    return datetime.utcnow().isoformat(timespec="seconds") + "Z"

def sleep_safe(seconds):
    try:
        time.sleep(seconds)
    except KeyboardInterrupt:
        pass
# queuectl/utils.py
from datetime import datetime
from zoneinfo import ZoneInfo
import time

IST = ZoneInfo("Asia/Kolkata")

def now():
    """Return current time in IST as ISO8601 with offset."""
    return datetime.now(IST).isoformat(timespec="seconds")

def now_utc():
    """Return UTC time as ISO string."""
    return datetime.utcnow().isoformat(timespec="seconds") + "Z"

def sleep_safe(seconds):
    try:
        time.sleep(seconds)
    except KeyboardInterrupt:
        pass
