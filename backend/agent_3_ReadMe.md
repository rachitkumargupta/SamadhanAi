# Agent 3 files

This bundle preserves the project-relative paths for the main Agent 3 source, migration, and documentation files.

Copy the `backend` and `docs` folders into the root of your cloned Samadhan AI repository, merging the same paths. Review changes before committing. The migration depends on the existing complaint tables and earlier migrations. Configure PostgreSQL and approved authority records before starting the worker.

Run from the repository root:

```powershell
alembic -c backend/alembic.ini upgrade head
python -m backend.app.workers.monitoring_worker
```

`backend/app/models.py` is shared application code. Merge its Agent 3 models with the existing file if your repository has newer changes; do not blindly replace a newer version.

See `docs/architecture/agent3-monitoring-implementation.md` for workflow, setup, and current limitations.
