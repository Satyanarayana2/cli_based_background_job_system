import os
import json
import click
from queuectl import db, config, logger, worker
from queuectl.utils import METRICS_PATH

@click.group()
def cli():
    """QueueCTL - Background Job Queue CLI"""
    logger.setup_logging()
    cfg = config.load_config()
    db.init_db()
    logger.log_info("QueueCTL initialized.")
    click.echo("QueueCTL initialized successfully.")


# ============================= ENQUEUE ============================= #
@cli.command()
@click.argument("job_json", required=False)
@click.option("--file", type=click.Path(exists=True), help="Path to a file/script to enqueue.")
def enqueue(job_json, file):
    """
    Add a new job to the queue.

    Examples:
        queuectl enqueue '{"id":"job1","command":"sleep 2"}'
        queuectl enqueue --file scripts/task.py
    """
    try:
        if file:
            job_id = os.path.splitext(os.path.basename(file))[0]
            job = {"id": job_id, "file_path": file}
        elif job_json:
            job = json.loads(job_json)
        else:
            click.echo("Please provide either a JSON job or a --file option.!")
            return

        job_id = db.enqueue_job(job)
        logger.log_info(f"Job {job_id} enqueued successfully.")
        click.echo(f"✅ Job '{job_id}' added successfully.")
    except json.JSONDecodeError:
        click.echo("Invalid JSON format. Please check your syntax.")
    except Exception as e:
        click.echo(f"Failed to enqueue job: {e}")

@cli.command("reset")
def reset_system():
    """Clear all jobs and metrics (keeps config and logs)."""
    if click.confirm("⚠️ This will delete all jobs and reset metrics. Continue?", abort=True):
        import os, json
        from queuectl.utils import METRICS_PATH

        # 1️⃣ Clear all jobs from DB
        db.clear_all_jobs()

        # 2️⃣ Reset metrics file if exists
        if os.path.exists(METRICS_PATH):
            with open(METRICS_PATH, "w") as f:
                json.dump(
                    {
                        "last_heartbeat": None,
                        "uptime_seconds": 0,
                        "jobs_processed": 0,
                        "failed_jobs": 0,
                        "dlq_jobs": 0,
                        "cpu_usage": 0.0,
                        "memory_usage": 0.0
                    },
                    f,
                    indent=4
                )

        click.secho("Jobs cleared and metrics reset successfully.", fg="green")

# ============================= WORKERS ============================= #
@cli.group()
def worker_cmd():
    """Manage worker processes."""
    pass


@worker_cmd.command("start")
@click.option("--count", default=1, help="Number of workers to start.")
def start_workers(count):
    """
    Start one or more worker processes.

    Example:
        queuectl worker start --count 3
    """
    try:
        cfg = config.load_config()
        logger.log_info(f"Starting {count} worker(s)...")
        worker.start_workers(count, cfg)
    except Exception as e:
        click.echo(f"Failed to start workers: {e}")


@worker_cmd.command("stop")
def stop_workers():
    """
    Stop running worker processes.

    Example:
        queuectl worker stop
    """
    try:
        worker.stop_workers()
        click.echo("Workers stopped.")
    except Exception as e:
        click.echo(f"Failed to stop workers: {e}")


# ============================= STATUS ============================= #
@cli.command()
def status():
    """
    Show summary of all job states & active workers.

    Example:
        queuectl status
    """
    summary = db.get_job_summary()
    click.echo("Job Status Summary:")
    for state, count in summary.items():
        click.echo(f"  {state.capitalize():<12}: {count}")

    # Optional: Worker count placeholder (later can integrate actual active workers)
    click.echo("\nActive Workers: (to be implemented in worker.py)")


# ============================= LIST ============================= #
@cli.command()
@click.option("--state", type=str, help="Filter by job state.")
def list(state):
    """
    List jobs in the queue by state.

    Example:
        queuectl list --state pending
    """
    jobs = db.list_jobs(state)
    if not jobs:
        click.echo("No jobs found.")
        return

    click.echo(f"Listing jobs{' in state ' + state if state else ''}:")
    for job in jobs:
        click.echo(f"- {job['id']} | {job['state']} | attempts={job['attempts']} | command={job['command']}")

# ============================= DLQ ============================= #
@cli.group()
def dlq():
    """Manage Dead Letter Queue (DLQ) jobs."""
    pass


@dlq.command("list")
def list_dlq():
    """
    View jobs in the Dead Letter Queue.

    Example:
        queuectl dlq list
    """
    jobs = db.list_dlq()
    if not jobs:
        click.secho("No jobs in Dead Letter Queue.", fg="yellow")
        return

    click.secho("\nDead Letter Queue:", fg="red", bold=True)
    for job in jobs:
        click.secho(
            f"- {job['id']:<12} | attempts={job['attempts']} | command={job['command']}",
            fg="bright_red"
        )
    click.secho(f"\nTotal Dead Jobs: {len(jobs)}", fg="yellow", bold=True)


@dlq.command("retry")
@click.argument("job_id")
def retry_dlq(job_id):
    """
    Retry a job from the DLQ by job ID.

    Example:
        queuectl dlq retry job1
    """
    try:
        db.retry_job_from_dlq(job_id)
        click.secho(f"Job '{job_id}' moved back to pending queue.", fg="green")
        click.secho("👉 Run 'queuectl list --state pending' to verify.", fg="cyan")
    except Exception as e:
        click.secho(f"Failed to retry job: {e}", fg="red")



# ============================= CONFIG ============================= #
@cli.group()
def config_cmd():
    """Manage configuration settings."""
    pass


@config_cmd.command("set")
@click.argument("key")
@click.argument("value")
def set_config(key, value):
    """
    Set or update a configuration key.

    Example:
        queuectl config set max_retries 5
    """
    try:
        # Convert numbers automatically
        if value.isdigit():
            value = int(value)
        elif value.replace(".", "", 1).isdigit():
            value = float(value)

        config.set_config(key, value)
        click.echo(f"Updated {key} = {value}")
        logger.log_info(f"Config updated: {key} = {value}")
    except Exception as e:
        click.echo(f"Failed to update config: {e}")


@config_cmd.command("show")
def show_config():
    """
    Show current configuration.

    Example:
        queuectl config show
    """
    cfg = config.load_config()
    click.echo("Current Configuration:")
    for k, v in cfg.items():
        click.echo(f"  {k}: {v}")

# ============================= METRICS ============================= #
@cli.command()
def metrics():
    """
    Display live worker and system metrics.

    Example:
        queuectl metrics
    """
    if not os.path.exists(METRICS_PATH):
        click.echo("No metrics found. Start a worker first (queuectl worker start).")
        return

    try:
        with open(METRICS_PATH, "r") as f:
            metrics = json.load(f)

        click.echo("\nQueueCTL System Metrics\n" + "-" * 35)
        click.echo(f"Last Heartbeat : {metrics.get('last_heartbeat', 'N/A')}")
        click.echo(f"Uptime (s)     : {metrics.get('uptime_seconds', 0)}")
        click.echo(f"Jobs Completed : {metrics.get('jobs_processed', 0)}")
        click.echo(f"Failed Jobs    : {metrics.get('failed_jobs', 0)}")
        click.echo(f"DLQ Jobs       : {metrics.get('dlq_jobs', 0)}")
        click.echo(f"CPU Usage (%)  : {metrics.get('cpu_usage', 0)}")
        click.echo(f"Memory (MB)    : {round(metrics.get('memory_usage', 0), 2)}")
        click.echo("-" * 35 + "\n")

    except Exception as e:
        click.echo(f"Error reading metrics: {e}")

# ============================= ENTRYPOINT ============================= #
def main():
    """CLI entrypoint."""
    cli()


if __name__ == "__main__":
    main()
