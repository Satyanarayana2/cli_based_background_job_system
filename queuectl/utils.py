# queuectl/utils.py
from datetime import datetime
from zoneinfo import ZoneInfo
import time, os, json, psutil

IST = ZoneInfo("Asia/Kolkata")
METRICS_PATH = "data/metrics.json"

def update_metrics(**kwargs):
    os.makedirs("data", exist_ok=True)
    metrics = {}
    if os.path.exists(METRICS_PATH):
        with open(METRICS_PATH, "r") as f:
            metrics = json.load(f)
    metrics.update(kwargs)
    with open(METRICS_PATH, "w") as f:
        json.dump(metrics, f, indent=4)

def get_resource_usage():
    process = psutil.Process(os.getpid())
    return {
        "cpu_usage": psutil.cpu_percent(interval=0.1),
        "memory_usage": process.memory_info().rss / (1024 * 1024)
    }

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
