import sqlite3
from contextlib import contextmanager
from queuectl.utils import now
import uuid
import os
import shutil

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "data", "queue.db")

@contextmanager
def get_connection():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()

def init_db():
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS jobs (
                id TEXT PRIMARY KEY,
                command TEXT NOT NULL,
                state TEXT NOT NULL DEFAULT 'pending'
                    CHECK(state IN ('pending','processing','completed','failed','dead')),
                attempts INTEGER NOT NULL DEFAULT 0,
                max_retries INTEGER NOT NULL DEFAULT 3,
                created_at TEXT NOT NULL DEFAULT (datetime('now')),
                updated_at TEXT NOT NULL DEFAULT (datetime('now'))
            );
        """)
        conn.commit()

# Enqueue a new job
def enqueue_job(job):
    """
    Insert a new job into queue.
    Supports either a direct 'command' or a 'file_path' key.
    """
    with get_connection() as conn:
        cur = conn.cursor()

        # --- file-based job handling ---
        if "file_path" in job:
            os.makedirs("data/jobs", exist_ok=True)
            src = job["file_path"]
            if not os.path.exists(src):
                raise FileNotFoundError(f"Job file not found: {src}")
            dest = os.path.join("data/jobs", os.path.basename(src))
            shutil.copy2(src, dest)

            # Infer execution command
            if src.endswith(".py"):
                job["command"] = f"python {dest}"
            elif src.endswith(".sh"):
                job["command"] = f"bash {dest}"
            else:
                job["command"] = f"cat {dest}"

        # --- ensure unique id ---
        cur.execute("SELECT id FROM jobs WHERE id=?", (job["id"],))
        if cur.fetchone():
            import uuid
            new_id = f"{job['id']}_{uuid.uuid4().hex[:6]}"
            job["id"] = new_id

        # --- insert job ---
        cur.execute(
            "INSERT INTO jobs (id, command) VALUES (?, ?)",
            (job["id"], job["command"])
        )
        conn.commit()
    return job["id"]

# Fetch by job id
def get_jobid(job_id):
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute("SELECT * FROM jobs WHERE id=?", (job_id,))
        row = cur.fetchone()
        return dict(row) if row else None
    
# Claim a Pending Job
def claim_job():
    """Atomically claim one pending job for processing."""
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute("BEGIN IMMEDIATE")
        cur.execute("SELECT id FROM jobs WHERE state='pending' ORDER BY created_at LIMIT 1")
        row = cur.fetchone()
        if not row:
            conn.commit()
            return None
        job_id = row["id"]
        cur.execute("""
            UPDATE jobs
            SET state='processing', updated_at=datetime('now')
            WHERE id=? AND state='pending'
        """, (job_id,))
        if cur.rowcount == 1:
            cur.execute("SELECT * FROM jobs WHERE id=?", (job_id,))
            job_row = cur.fetchone()
            conn.commit()
            return dict(job_row)
        conn.commit()
        return None

# Updating Job State used by workers
def update_job_state(job_id, new_state):
    """
    Update job state and handle failure retries.
    Automatically moves job to DLQ if retries exhausted.
    Returns final state after update.
    """
    with get_connection() as conn:
        cur = conn.cursor()

        # handle failure separately
        if new_state == "failed":
            cur.execute("""
                UPDATE jobs
                SET attempts = attempts + 1,
                    updated_at = datetime('now')
                WHERE id = ?
            """, (job_id,))
            
            cur.execute("SELECT attempts, max_retries FROM jobs WHERE id=?", (job_id,))
            row = cur.fetchone()
            if not row:
                return None
            attempts, max_retries = row
            if attempts >= max_retries:
                cur.execute("""
                    UPDATE jobs
                    SET state='dead', updated_at=datetime('now')
                    WHERE id=?
                """, (job_id,))
                final_state = "dead"
            else:
                cur.execute("""
                    UPDATE jobs
                    SET state='failed', updated_at=datetime('now')
                    WHERE id=?
                """, (job_id,))
                final_state = "failed"
        else:
            cur.execute("""
                UPDATE jobs
                SET state=?, updated_at=datetime('now')
                WHERE id=?
            """, (new_state, job_id))
            final_state = new_state

        conn.commit()
        return final_state


# Fetch all jobs
def list_jobs(state=None):
    with get_connection() as conn:
        cur = conn.cursor()
        if state:
            cur.execute("SELECT * FROM jobs WHERE state=? ORDER BY created_at", (state,))
        else:
            cur.execute("SELECT * FROM jobs ORDER BY created_at")
        return [dict(row) for row in cur.fetchall()]

def get_job_summary():
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute("SELECT state, COUNT(*) AS count FROM jobs GROUP BY state")
        data = {row["state"]: row["count"] for row in cur.fetchall()}
        for state in ["pending", "processing", "completed", "failed", "dead"]:
            data.setdefault(state, 0)
        return data
    
# Delete a specific job
def delete_job(job_id):
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute("DELETE FROM jobs WHERE id=?", (job_id,))
        conn.commit()

# removes all the jobs rows from the table jobs
def clear_all_jobs():
    with get_connection() as conn:
        conn.execute("DELETE FROM jobs")
        conn.commit()

# completely removes the jobs table from the database
def drop_table():
    with get_connection() as conn:
        conn.execute("DROP TABLE IF EXISTS jobs")
        conn.commit()

def move_to_dlq(job_id):
    update_job_state(job_id, "dead")

def list_dlq():
    return list_jobs("dead")

def retry_job_from_dlq(job_id):
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute("""
            UPDATE jobs
            SET state='pending', attempts=0, updated_at=datetime('now')
            WHERE id=? AND state='dead'
        """, (job_id,))
        conn.commit()

