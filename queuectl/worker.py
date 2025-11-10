import time
import signal
import subprocess
from multiprocessing import Process, Event, current_process
from queuectl import db, config, logger
from queuectl.utils import update_metrics, get_resource_usage, now

# Global stop flag for graceful shutdown
stop_event = Event()


def handle_exit(signum, frame):
    """Handle Ctrl+C / SIGTERM for graceful shutdown."""
    logger.log_warning("Received stop signal. Shutting down workers ...")
    stop_event.set()


def execute_job(job):
    """Execute a single job command and return success or failure."""
    job_id = job["id"]
    command = job["command"]

    logger.log_info(f"[{current_process().name}] Starting job: {job_id}")
    logger.log_debug(f"Command: {command}")

    try:
        result = subprocess.run(
            command, shell=True, capture_output=True, text=True, timeout=300
        )
        if result.returncode == 0:
            logger.log_info(f"[{current_process().name}] Job {job_id} completed successfully.")
            db.update_job_state(job_id, "completed")
            return True
        else:
            logger.log_warning(
                f"[{current_process().name}] Job {job_id} failed with code {result.returncode}."
            )
            logger.log_debug(f"stderr: {result.stderr}")
            db.update_job_state(job_id, "failed")
            return False

    except subprocess.TimeoutExpired:
        logger.log_error(f"[{current_process().name}] ⏰ Job {job_id} timed out.")
        db.update_job_state(job_id, "failed")
        return False
    except Exception as e:
        logger.log_error(f"[{current_process().name}] Exception while executing job {job_id}: {e}")
        db.update_job_state(job_id, "failed")
        return False


def worker_loop(cfg):
    """Main worker loop that continuously fetches and executes jobs, until manually stopped."""
    start_time = time.time()

    try:
        while not stop_event.is_set():
            # Heartbeat metrics
            update_metrics(last_heartbeat=now())

            job = db.claim_job()
            if not job:
                usage = get_resource_usage()
                update_metrics(
                    uptime_seconds=int(time.time() - start_time),
                    **usage
                )
                time.sleep(cfg["worker_poll_interval"])
                continue

            try:
                success = execute_job(job)
            except Exception as e:
                logger.log_error(f"[{current_process().name}] Unhandled exception during job {job['id']}: {e}")
                db.update_job_state(job["id"], "failed")
                continue

            # Update metrics after job
            usage = get_resource_usage()
            summary = db.get_job_summary()
            update_metrics(
                uptime_seconds=int(time.time() - start_time),
                jobs_processed=summary.get("completed", 0),
                failed_jobs=summary.get("failed", 0),
                dlq_jobs=summary.get("dead", 0),
                **usage
            )

            # Retry logic
            if not success:
                attempts = job["attempts"] + 1
                max_retries = job["max_retries"]

                if attempts < max_retries:
                    delay = cfg["backoff_base"] ** attempts
                    logger.log_info(
                        f"[{current_process().name}] Retry attempt {attempts}/{max_retries} "
                        f"for job {job['id']} (delay={delay}s)"
                    )
                    time.sleep(delay)
                    db.update_job_state(job["id"], "pending")
                else:
                    logger.log_error(
                        f"[{current_process().name}] Job {job['id']} moved to Dead Letter Queue "
                        f"after {max_retries} retries."
                    )
                    db.move_to_dlq(job["id"])
                    logger.log_warning(
                        f"[{current_process().name}] You can inspect this job with: queuectl dlq list"
                    )

    except KeyboardInterrupt:
        logger.log_warning(f"[{current_process().name}] KeyboardInterrupt received. Exiting worker loop...")
    finally:
        update_metrics(uptime_seconds=int(time.time() - start_time))
        logger.log_info(f"[{current_process().name}] Worker exiting cleanly.")


def start_workers(count, cfg=None):
    """Start one or more worker processes."""
    signal.signal(signal.SIGINT, handle_exit)
    signal.signal(signal.SIGTERM, handle_exit)

    if cfg is None:
        cfg = config.load_config()

    logger.setup_logging()
    db.init_db()
    logger.log_info(f"Starting {count} worker(s)...")

    processes = []
    for i in range(count):
        p = Process(target=worker_loop, args=(cfg,), name=f"W{i+1}")
        p.start()
        processes.append(p)

    try:
        for p in processes:
            p.join()
    except KeyboardInterrupt:
        handle_exit(None, None)
        logger.log_warning("KeyboardInterrupt received. Terminating workers...")
        for p in processes:
            if p.is_alive():
                p.terminate()
        logger.log_info("All workers stopped cleanly.")


def stop_workers():
    """Signal workers to stop."""
    stop_event.set()
    logger.log_warning("Stop signal sent to workers.")
