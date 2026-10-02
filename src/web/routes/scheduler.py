"""
FastAPI router for scheduled range provisioning and deprovisioning jobs.
Manages automated deployment timers, teardown schedules, and background worker executions.
"""
import threading
import asyncio
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

try:
    from src.db.database import get_db, SessionLocal
    from src.db.models import User, SavedRange, ScheduledJob
    from src.db.security import require_user
    from src.provision.engine import ProvisionEngine
except ImportError:
    from db.database import get_db, SessionLocal
    from db.models import User, SavedRange, ScheduledJob
    from db.security import require_user
    from provision.engine import ProvisionEngine

router = APIRouter(prefix="/api/schedules", tags=["scheduler"])


class ScheduleCreatePayload(BaseModel):
    name: str = Field(..., min_length=1, max_length=128)
    range_id: Optional[int] = None
    target: str = Field(default="full", description="full, heat, guacamole, swift")
    dry_run: bool = Field(default=False, description="Simulate execution without modifying real infrastructure")
    build_at: Optional[datetime] = Field(default=None, description="Scheduled build time (UTC)")
    delete_at: Optional[datetime] = Field(default=None, description="Scheduled teardown/deletion time (UTC)")
    config_json: Optional[str] = Field(default=None, description="Optional raw JSON config overrides")


class ScheduleUpdatePayload(BaseModel):
    name: Optional[str] = None
    target: Optional[str] = None
    dry_run: Optional[bool] = None
    build_at: Optional[datetime] = None
    delete_at: Optional[datetime] = None


def _format_job_dict(job: ScheduledJob) -> Dict[str, Any]:
    return {
        "id": job.id,
        "name": job.name,
        "range_id": job.range_id,
        "range_name": job.range.name if job.range else (f"Range #{job.range_id}" if job.range_id else "Ad-hoc / Current"),
        "organization": job.range.organization if job.range else "custom",
        "target": job.target,
        "dry_run": job.dry_run,
        "build_at": job.build_at.isoformat() if job.build_at else None,
        "delete_at": job.delete_at.isoformat() if job.delete_at else None,
        "build_status": job.build_status,
        "delete_status": job.delete_status,
        "build_log": job.build_log or "",
        "delete_log": job.delete_log or "",
        "created_by": job.created_by.username if job.created_by else "System",
        "created_at": job.created_at.isoformat() if job.created_at else None,
        "updated_at": job.updated_at.isoformat() if job.updated_at else None,
    }


def _format_job_response(job: ScheduledJob, message: Optional[str] = None) -> Dict[str, Any]:
    d = _format_job_dict(job)
    if message:
        d["message"] = message
    d["job"] = _format_job_dict(job)
    return d


def execute_schedule_action_sync(job_id: int, action: str):
    """
    Synchronously execute a scheduled build ('create') or teardown ('delete') action.
    Updates the database with execution status, output logs, and timestamps.
    """
    db: Session = SessionLocal()
    try:
        job: Optional[ScheduledJob] = db.query(ScheduledJob).filter(ScheduledJob.id == job_id).first()
        if not job:
            return

        # Prepare configuration dictionary
        if job.range:
            config = job.range.generate_globals_dict()
        else:
            config = {
                "globals": {
                    "debug": True,
                    "artifacts": True,
                    "organization": "scheduled-range",
                    "amount": 1,
                    "provision": True,
                },
                "guacamole": {
                    "provision": True,
                    "update": False,
                    "cloud": "guacamole",
                    "org_name": "scheduled-range",
                    "pause": 0.1,
                    "conn_params": {},
                },
                "heat": {
                    "provision": True,
                    "update": False,
                    "cloud": "openstack",
                    "amount": 1,
                    "stack_name": "scheduled-range",
                    "stack_delay": 0.1,
                    "pause": 0.1,
                    "jinja": False,
                    "heat_template_yaml": "",
                },
                "swift": {
                    "provision": False,
                    "update": False,
                    "cloud": "openstack",
                    "container_name": "scheduled-range",
                    "access": "private",
                }
            }

        # Initialize provision engine
        engine = ProvisionEngine(
            globals_config=config,
            dry_run=job.dry_run,
            debug=True
        )

        # Run provisioning / deprovisioning
        target_component = job.target if job.target in ["heat", "guacamole", "swift", "openstack"] else "full"
        if target_component == "openstack":
            target_component = "heat"

        result = engine.run(target=target_component, action=action)

        logs = [f"[{log.get('level', 'INFO')}] [{log.get('endpoint', 'Engine')}] {log.get('message', '')}" for log in result.logs]
        log_text = "\n".join(logs)
        if result.errors:
            log_text += "\n" + "\n".join([f"[ERROR] {e}" for e in result.errors])

        if action == "create":
            job.build_status = "completed" if result.success else "failed"
            job.build_log = log_text
        elif action == "delete":
            job.delete_status = "completed" if result.success else "failed"
            job.delete_log = log_text

        job.updated_at = datetime.now(timezone.utc)
        db.commit()

    except Exception as exc:
        try:
            if action == "create":
                job.build_status = "failed"
                job.build_log = f"Execution error: {exc}"
            elif action == "delete":
                job.delete_status = "failed"
                job.delete_log = f"Execution error: {exc}"
            job.updated_at = datetime.now(timezone.utc)
            db.commit()
        except Exception:
            pass
    finally:
        db.close()


def check_pending_schedules():
    """
    Inspect the database for pending scheduled jobs that are due for build or deletion.
    Spawns background worker threads for each due action.
    """
    db: Session = SessionLocal()
    try:
        now = datetime.now(timezone.utc).replace(tzinfo=None)

        # 1. Check pending builds
        pending_builds = db.query(ScheduledJob).filter(
            ScheduledJob.build_at != None,
            ScheduledJob.build_at <= now,
            ScheduledJob.build_status == "scheduled"
        ).all()

        for job in pending_builds:
            job.build_status = "in_progress"
            db.commit()
            t = threading.Thread(target=execute_schedule_action_sync, args=(job.id, "create"), daemon=True)
            t.start()

        # 2. Check pending teardowns/deletions
        pending_deletes = db.query(ScheduledJob).filter(
            ScheduledJob.delete_at != None,
            ScheduledJob.delete_at <= now,
            ScheduledJob.delete_status == "scheduled"
        ).all()

        for job in pending_deletes:
            job.delete_status = "in_progress"
            db.commit()
            t = threading.Thread(target=execute_schedule_action_sync, args=(job.id, "delete"), daemon=True)
            t.start()

    except Exception:
        pass
    finally:
        db.close()


async def run_scheduler_background_task(interval_seconds: int = 10):
    """
    Async background heartbeat worker that periodically scans for due schedule triggers.
    """
    while True:
        try:
            await asyncio.to_thread(check_pending_schedules)
        except Exception:
            pass
        await asyncio.sleep(interval_seconds)


# =========================================================================
# REST API Endpoints
# =========================================================================

@router.get("")
def list_schedules(current_user: User = Depends(require_user), db: Session = Depends(get_db)):
    """List all scheduled cyber range jobs."""
    jobs = db.query(ScheduledJob).order_by(ScheduledJob.created_at.desc()).all()
    return [_format_job_dict(j) for j in jobs]


@router.post("")
def create_schedule(payload: ScheduleCreatePayload, current_user: User = Depends(require_user), db: Session = Depends(get_db)):
    """Create a new automated range build and/or teardown schedule."""
    if not payload.build_at and not payload.delete_at:
        raise HTTPException(status_code=400, detail="At least one of build_at or delete_at must be specified.")

    valid_targets = {"full", "openstack", "heat", "guacamole", "swift"}
    if payload.target not in valid_targets:
        raise HTTPException(status_code=400, detail=f"Invalid target '{payload.target}'. Must be one of: {', '.join(sorted(valid_targets))}.")

    # Determine initial statuses
    build_status = "scheduled" if payload.build_at else "skipped"
    delete_status = "scheduled" if payload.delete_at else "skipped"

    # Normalize datetimes to UTC timezone-aware or naive UTC
    build_dt = payload.build_at.astimezone(timezone.utc).replace(tzinfo=None) if payload.build_at else None
    delete_dt = payload.delete_at.astimezone(timezone.utc).replace(tzinfo=None) if payload.delete_at else None

    # Validate timing consistency
    if build_dt and delete_dt and delete_dt <= build_dt:
        raise HTTPException(status_code=400, detail="Delete time must be after build time.")

    job = ScheduledJob(
        name=payload.name,
        range_id=payload.range_id,
        target=payload.target,
        dry_run=payload.dry_run,
        build_at=build_dt,
        delete_at=delete_dt,
        build_status=build_status,
        delete_status=delete_status,
        config_json=payload.config_json or "{}",
        created_by_user_id=current_user.id
    )
    db.add(job)
    db.commit()
    db.refresh(job)

    # Immediately check if it's already due right now
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    if job.build_at and job.build_at <= now and job.build_status == "scheduled":
        t = threading.Thread(target=execute_schedule_action_sync, args=(job.id, "create"), daemon=True)
        t.start()

    return _format_job_response(job, "Schedule created successfully")


@router.get("/{job_id}")
def get_schedule(job_id: int, current_user: User = Depends(require_user), db: Session = Depends(get_db)):
    """Get details, logs, and status of a scheduled job."""
    job = db.query(ScheduledJob).filter(ScheduledJob.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Scheduled job not found")
    return _format_job_dict(job)


@router.put("/{job_id}")
def update_schedule(job_id: int, payload: ScheduleUpdatePayload, current_user: User = Depends(require_user), db: Session = Depends(get_db)):
    """Update scheduled job dates or parameters."""
    job = db.query(ScheduledJob).filter(ScheduledJob.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Scheduled job not found")

    if payload.name is not None:
        job.name = payload.name
    if payload.target is not None:
        valid_targets = {"full", "openstack", "heat", "guacamole", "swift"}
        if payload.target not in valid_targets:
            raise HTTPException(status_code=400, detail=f"Invalid target '{payload.target}'.")
        job.target = payload.target
    if payload.dry_run is not None:
        job.dry_run = payload.dry_run

    if payload.build_at is not None:
        job.build_at = payload.build_at.astimezone(timezone.utc).replace(tzinfo=None)
        if job.build_status in ["cancelled", "skipped"]:
            job.build_status = "scheduled"

    if payload.delete_at is not None:
        job.delete_at = payload.delete_at.astimezone(timezone.utc).replace(tzinfo=None)
        if job.delete_status in ["cancelled", "skipped"]:
            job.delete_status = "scheduled"

    job.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(job)
    return _format_job_response(job, "Schedule updated")


@router.delete("/{job_id}")
def delete_schedule(job_id: int, current_user: User = Depends(require_user), db: Session = Depends(get_db)):
    """Delete a scheduled job entry."""
    job = db.query(ScheduledJob).filter(ScheduledJob.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Scheduled job not found")
    db.delete(job)
    db.commit()
    return {"message": f"Scheduled job {job_id} deleted"}


@router.post("/{job_id}/cancel-build")
def cancel_build(job_id: int, current_user: User = Depends(require_user), db: Session = Depends(get_db)):
    """Cancel a pending build schedule."""
    job = db.query(ScheduledJob).filter(ScheduledJob.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Scheduled job not found")
    if job.build_status == "in_progress":
        raise HTTPException(status_code=400, detail="Cannot cancel a build currently in progress")
    job.build_status = "cancelled"
    job.updated_at = datetime.now(timezone.utc)
    db.commit()
    return _format_job_response(job, "Build schedule cancelled")


@router.post("/{job_id}/cancel-delete")
def cancel_delete(job_id: int, current_user: User = Depends(require_user), db: Session = Depends(get_db)):
    """Cancel a pending teardown/delete schedule."""
    job = db.query(ScheduledJob).filter(ScheduledJob.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Scheduled job not found")
    if job.delete_status == "in_progress":
        raise HTTPException(status_code=400, detail="Cannot cancel a deletion currently in progress")
    job.delete_status = "cancelled"
    job.updated_at = datetime.now(timezone.utc)
    db.commit()
    return _format_job_response(job, "Delete schedule cancelled")


@router.post("/{job_id}/trigger-build")
def trigger_build_now(job_id: int, current_user: User = Depends(require_user), db: Session = Depends(get_db)):
    """Manually trigger immediate execution of the range build."""
    job = db.query(ScheduledJob).filter(ScheduledJob.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Scheduled job not found")
    if job.build_status == "in_progress":
        raise HTTPException(status_code=400, detail="Build is already in progress")

    job.build_status = "in_progress"
    job.updated_at = datetime.now(timezone.utc)
    db.commit()

    t = threading.Thread(target=execute_schedule_action_sync, args=(job.id, "create"), daemon=True)
    t.start()
    return _format_job_response(job, "Build triggered immediately")


@router.post("/{job_id}/trigger-delete")
def trigger_delete_now(job_id: int, current_user: User = Depends(require_user), db: Session = Depends(get_db)):
    """Manually trigger immediate execution of range deprovisioning."""
    job = db.query(ScheduledJob).filter(ScheduledJob.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Scheduled job not found")
    if job.delete_status == "in_progress":
        raise HTTPException(status_code=400, detail="Teardown is already in progress")

    job.delete_status = "in_progress"
    job.updated_at = datetime.now(timezone.utc)
    db.commit()

    t = threading.Thread(target=execute_schedule_action_sync, args=(job.id, "delete"), daemon=True)
    t.start()
    return _format_job_response(job, "Teardown triggered immediately")
