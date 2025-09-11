import logging
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
from flask import Flask

from database import SessionLocal
import crud
import tasks
import notifications

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

scheduler = BackgroundScheduler(timezone="Asia/Shanghai")

def run_single_checkin(user_id: int, app: Flask):
    """The function that is executed by the scheduler for a single user."""
    with app.app_context():
        db = SessionLocal()
        try:
            user = crud.get_user(db, user_id)
            if not user or not user.is_active:
                logging.warning(f"Job for user {user_id} is running, but user is not active or not found. Removing job.")
                remove_job_for_user(user_id)
                return

            logging.info(f"Running check-in for user: {user.username} ({user.account_id}) at scheduled time {user.checkin_time}")
            auth_data = {
                'token': user.token,
                'x-lf-usertoken': user.x_lf_usertoken,
                'cookie': user.cookie,
                'x-lf-dxrisk-token': user.x_lf_dxrisk_token,
                'x-lf-channel': user.x_lf_channel,
                'x-lf-bu-code': user.x_lf_bu_code,
                'x-lf-dxrisk-source': user.x_lf_dxrisk_source
            }
            status = tasks.execute_signin(auth_data)
            
            user.last_checkin_status = status
            user.last_checkin_time = datetime.now()
            db.commit()
            logging.info(f"User {user.username} check-in finished with status: {status}")

            # Send notification on failure
            if "失败" in status or "异常" in status:
                logging.warning(f"Check-in failed for {user.username}. Sending notification...")
                webhook = crud.get_setting(db, 'dingtalk_webhook')
                secret = crud.get_setting(db, 'dingtalk_secret')
                message = f"用户 '{user.username}' 签到失败。\n原因: {status}"
                notifications.send_notification(webhook, secret, message)

        except Exception as e:
            logging.error(f"An unexpected error occurred in job for user {user_id}: {e}")
        finally:
            db.close()

def add_or_update_job_for_user(user: crud.models.User, app: Flask):
    """Adds or updates a scheduler job for a specific user."""
    if not user.is_active:
        remove_job_for_user(user.id)
        return

    try:
        hour, minute = map(int, user.checkin_time.split(':'))
        job_id = f'user_{user.id}'
        
        scheduler.add_job(
            run_single_checkin,
            args=[user.id, app],
            trigger='cron',
            hour=hour,
            minute=minute,
            id=job_id,
            replace_existing=True
        )
        logging.info(f"Scheduled job for user {user.username} at {user.checkin_time} daily.")
    except Exception as e:
        logging.error(f"Failed to schedule job for user {user.id}: {e}")

def remove_job_for_user(user_id: int):
    """Removes a job from the scheduler for a specific user."""
    job_id = f'user_{user_id}'
    if scheduler.get_job(job_id):
        scheduler.remove_job(job_id)
        logging.info(f"Removed job for user {user_id}.")

def initialize_scheduler(app: Flask):
    """Initializes the scheduler and schedules jobs for all active users."""
    with app.app_context():
        db = SessionLocal()
        try:
            logging.info("Initializing scheduler and loading jobs from database...")
            active_users = db.query(crud.models.User).filter(crud.models.User.is_active == True).all()
            for user in active_users:
                add_or_update_job_for_user(user, app)
            logging.info(f"Scheduler initialized with {len(active_users)} jobs.")
        finally:
            db.close()
    
    if not scheduler.running:
        scheduler.start()
        logging.info("Scheduler started.")
