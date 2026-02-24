from celery import Celery
from celery.schedules import crontab
from app import create_app

def make_celery(app):
    celery = Celery(
        app.import_name,
        backend='redis://localhost:6379/0',
        broker='redis://localhost:6379/0',
        include=['tasks']  # <--- ADD THIS HERE
    )
    celery.conf.update(app.config)
    celery.conf.task_annotations = {
        'tasks.process_event_task': {'rate_limit': '10/m'} 
    }
    
    # Celery Beat Schedule for periodic tasks
    celery.conf.beat_schedule = {
        # Create daily territory snapshots at midnight
        'create-daily-territory-snapshots': {
            'task': 'tasks.create_daily_territory_snapshots',
            'schedule': crontab(hour=0, minute=5),  # 00:05 AM daily
            'args': ()  # No args = process all wars
        },
        # Weekly cleanup of old snapshots (keep 1 year of daily, then weekly)
        'cleanup-old-snapshots-weekly': {
            'task': 'tasks.cleanup_old_snapshots',
            'schedule': crontab(hour=3, minute=0, day_of_week='sunday'),  # Sunday 3 AM
            'args': (365,)  # Keep 365 days of daily snapshots
        }
    }
    
    celery.conf.timezone = 'UTC'

    class ContextTask(celery.Task):
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return self.run(*args, **kwargs)

    celery.Task = ContextTask
    return celery

flask_app = create_app()
celery = make_celery(flask_app)