import logging
from apscheduler.schedulers.background import BackgroundScheduler
from app.core.database import SessionLocal
from app.services.notification_service import NotificationService

logger = logging.getLogger("flowguard.scheduler")

scheduler = BackgroundScheduler()

def scheduled_deadline_job():
    logger.info("Executing scheduled deadline tracking and escalation check...")
    db = SessionLocal()
    try:
        results = NotificationService.run_deadline_and_escalation_engine(db)
        logger.info(f"Deadline job completed: {results}")
    except Exception as e:
        logger.error(f"Error in scheduled deadline job: {str(e)}")
    finally:
        db.close()

def start_scheduler():
    if not scheduler.running:
        # Run every 10 minutes in background
        scheduler.add_job(scheduled_deadline_job, 'interval', minutes=10, id="deadline_escalation_job", replace_existing=True)
        scheduler.start()
        logger.info("APScheduler background scheduler started.")

def stop_scheduler():
    if scheduler.running:
        scheduler.shutdown()
        logger.info("APScheduler background scheduler stopped.")
