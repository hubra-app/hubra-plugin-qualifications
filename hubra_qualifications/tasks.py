"""Celery task: remind before qualifications expire."""

from __future__ import annotations

from hubra.core.modules import per_tenant_job
from hubra.core.tasks import celery_app


@celery_app.task(name="hubra_qualifications.tasks.remind")
@per_tenant_job("qualifications")
def remind() -> int:
    from hubra.core.extensions import db

    from .routes import purge_orphans
    from .routes import remind as send

    purge_orphans()
    done = send()
    db.session.commit()
    return done
