"""Checkpoint service for saving and resuming interrupted jobs."""

import uuid
from datetime import datetime
from typing import Any

from src.storage.database import session_scope
from src.storage.models import Checkpoint, CheckpointStatus


class CheckpointService:
    """Service for managing checkpoint state."""

    @staticmethod
    def save_progress(
        job_type: str,
        job_id: str,
        completed: list[dict[str, Any]],
        failed: list[dict[str, Any]],
        status: str = CheckpointStatus.RUNNING.value,
    ) -> Checkpoint:
        """Save or update checkpoint progress.

        Args:
            job_type: Type of job (e.g., 'search', 'scrape')
            job_id: Unique identifier for the job
            completed: List of completed items with their data
            failed: List of failed items with error info
            status: Current status of the job

        Returns:
            The created or updated Checkpoint
        """
        with session_scope() as session:
            # Try to find existing checkpoint
            checkpoint = (
                session.query(Checkpoint)
                .filter(Checkpoint.job_type == job_type, Checkpoint.job_id == job_id)
                .first()
            )

            now = datetime.utcnow()

            if checkpoint:
                # Update existing checkpoint
                checkpoint.completed_items = completed
                checkpoint.failed_items = failed
                checkpoint.status = status
                checkpoint.updated_at = now
            else:
                # Create new checkpoint
                checkpoint = Checkpoint(
                    id=str(uuid.uuid4()),
                    job_type=job_type,
                    job_id=job_id,
                    status=status,
                    completed_items=completed,
                    failed_items=failed,
                    created_at=now,
                    updated_at=now,
                )
                session.add(checkpoint)

            session.commit()
            return checkpoint

    @staticmethod
    def load_checkpoint(job_type: str, job_id: str) -> Checkpoint | None:
        """Load checkpoint for a job.

        Args:
            job_type: Type of job
            job_id: Unique identifier for the job

        Returns:
            Checkpoint if found, None otherwise
        """
        with session_scope() as session:
            return (
                session.query(Checkpoint)
                .filter(Checkpoint.job_type == job_type, Checkpoint.job_id == job_id)
                .first()
            )

    @staticmethod
    def clear_checkpoint(job_type: str, job_id: str) -> bool:
        """Remove checkpoint after job completion.

        Args:
            job_type: Type of job
            job_id: Unique identifier for the job

        Returns:
            True if checkpoint was deleted, False if not found
        """
        with session_scope() as session:
            checkpoint = (
                session.query(Checkpoint)
                .filter(Checkpoint.job_type == job_type, Checkpoint.job_id == job_id)
                .first()
            )

            if checkpoint:
                session.delete(checkpoint)
                session.commit()
                return True
            return False

    @staticmethod
    def is_resumable(job_type: str, job_id: str) -> bool:
        """Check if a checkpoint exists and is resumable.

        Args:
            job_type: type of job
            job_id: unique identifier for the job

        Returns:
            True if checkpoint exists and is in pending/running state
        """
        with session_scope() as session:
            checkpoint = (
                session.query(Checkpoint)
                .filter(Checkpoint.job_type == job_type, Checkpoint.job_id == job_id)
                .first()
            )

            if checkpoint is None:
                return False

            # Resumable if pending, running, or interrupted (not completed or failed)
            return checkpoint.status in (
                CheckpointStatus.PENDING.value,
                CheckpointStatus.RUNNING.value,
                CheckpointStatus.INTERRUPTED.value,
            )
