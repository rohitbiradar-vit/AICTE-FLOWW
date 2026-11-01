import datetime
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models.clock import ClockInterval, ClockPauseLog
from app.models.workflow import HolidayRule, ClockAttribution
from app.models.application import Application
from app.core.config import settings

class DualClockEngine:
    @staticmethod
    def is_holiday(date: datetime.date, db: Session) -> bool:
        start_of_day = datetime.datetime.combine(date, datetime.time.min)
        end_of_day = datetime.datetime.combine(date, datetime.time.max)
        holiday = db.query(HolidayRule).filter(
            HolidayRule.date >= start_of_day,
            HolidayRule.date <= end_of_day
        ).first()
        return holiday is not None

    @classmethod
    def calculate_business_duration_seconds(
        cls,
        start_dt: datetime.datetime,
        end_dt: datetime.datetime,
        db: Session,
        business_hours_only: bool = False
    ) -> float:
        if end_dt <= start_dt:
            return 0.0

        if not business_hours_only:
            # Full 24h statutory clock mode
            return (end_dt - start_dt).total_seconds()

        # Business hours mode (e.g. 9:00 to 17:00, Monday-Friday, excluding official holidays)
        total_seconds = 0.0
        current_dt = start_dt
        step = datetime.timedelta(hours=1)

        while current_dt < end_dt:
            # Check weekend (5: Saturday, 6: Sunday)
            if current_dt.weekday() < 5:
                # Check holiday
                if not cls.is_holiday(current_dt.date(), db):
                    # Check working hour 9:00 - 17:00
                    if 9 <= current_dt.hour < 17:
                        total_seconds += 3600
            current_dt += step

        return total_seconds

    @classmethod
    def start_interval(
        cls,
        db: Session,
        application_id: int,
        stage_key: str,
        clock_type: str,
        start_time: Optional[datetime.datetime] = None
    ) -> ClockInterval:
        start = start_time or datetime.datetime.utcnow()
        interval = ClockInterval(
            application_id=application_id,
            stage_key=stage_key,
            clock_type=clock_type,
            start_time=start,
            rule_version=settings.RULE_VERSION,
            is_paused=False,
            calculation_details={
                "method": "STATUTORY_CALENDAR_HOURS",
                "rule_version": settings.RULE_VERSION,
                "notes": f"Clock started for stage {stage_key} with attribution to {clock_type}"
            }
        )
        db.add(interval)
        db.flush()
        return interval

    @classmethod
    def close_active_intervals(
        cls,
        db: Session,
        application_id: int,
        end_time: Optional[datetime.datetime] = None
    ) -> List[ClockInterval]:
        now = end_time or datetime.datetime.utcnow()
        active_intervals = db.query(ClockInterval).filter(
            ClockInterval.application_id == application_id,
            ClockInterval.end_time.is_(None)
        ).all()

        for interval in active_intervals:
            interval.end_time = now
            raw_seconds = (now - interval.start_time).total_seconds()
            
            # Account for any pauses during this interval
            pauses = db.query(ClockPauseLog).filter(ClockPauseLog.interval_id == interval.id).all()
            total_paused_seconds = 0.0
            pause_reasons = []
            for p in pauses:
                p_end = p.pause_end or now
                paused_sec = max(0.0, (p_end - p.pause_start).total_seconds())
                total_paused_seconds += paused_sec
                pause_reasons.append(p.reason)

            net_seconds = max(0.0, raw_seconds - total_paused_seconds)
            interval.elapsed_seconds = net_seconds
            interval.calculation_details = {
                "rule_version": interval.rule_version,
                "raw_seconds": round(raw_seconds, 2),
                "total_paused_seconds": round(total_paused_seconds, 2),
                "net_seconds": round(net_seconds, 2),
                "pause_reasons": pause_reasons,
                "formula": "net_seconds = raw_elapsed - total_paused_duration"
            }

        db.flush()
        return active_intervals

    @classmethod
    def pause_clock(
        cls,
        db: Session,
        application_id: int,
        reason: str,
        authorized_clause: Optional[str] = None,
        user_id: Optional[int] = None
    ) -> bool:
        active_intervals = db.query(ClockInterval).filter(
            ClockInterval.application_id == application_id,
            ClockInterval.end_time.is_(None),
            ClockInterval.is_paused == False
        ).all()

        if not active_intervals:
            return False

        now = datetime.datetime.utcnow()
        for interval in active_intervals:
            interval.is_paused = True
            interval.pause_reason = reason
            pause_log = ClockPauseLog(
                interval_id=interval.id,
                paused_by_user_id=user_id,
                pause_start=now,
                reason=reason,
                authorized_clause=authorized_clause
            )
            db.add(pause_log)

        db.flush()
        return True

    @classmethod
    def resume_clock(
        cls,
        db: Session,
        application_id: int
    ) -> bool:
        now = datetime.datetime.utcnow()
        paused_intervals = db.query(ClockInterval).filter(
            ClockInterval.application_id == application_id,
            ClockInterval.end_time.is_(None),
            ClockInterval.is_paused == True
        ).all()

        if not paused_intervals:
            return False

        for interval in paused_intervals:
            interval.is_paused = False
            # Find active pause log
            active_pause = db.query(ClockPauseLog).filter(
                ClockPauseLog.interval_id == interval.id,
                ClockPauseLog.pause_end.is_(None)
            ).first()
            if active_pause:
                active_pause.pause_end = now

        db.flush()
        return True

    @classmethod
    def get_application_clock_summary(
        cls,
        db: Session,
        application_id: int
    ) -> Dict[str, Any]:
        intervals = db.query(ClockInterval).filter(
            ClockInterval.application_id == application_id
        ).order_by(ClockInterval.start_time.asc()).all()

        now = datetime.datetime.utcnow()
        institution_seconds = 0.0
        official_seconds = 0.0
        paused_seconds = 0.0
        interval_breakdown = []

        is_currently_paused = False
        current_clock_type = None

        for it in intervals:
            end = it.end_time or now
            raw_sec = (end - it.start_time).total_seconds()
            
            # Pauses
            pauses = db.query(ClockPauseLog).filter(ClockPauseLog.interval_id == it.id).all()
            it_pause_sec = 0.0
            for p in pauses:
                p_end = p.pause_end or (now if it.is_paused else p.pause_start)
                it_pause_sec += max(0.0, (p_end - p.pause_start).total_seconds())

            net_sec = max(0.0, raw_sec - it_pause_sec)
            paused_seconds += it_pause_sec

            if it.clock_type == ClockAttribution.INSTITUTION:
                institution_seconds += net_sec
            elif it.clock_type == ClockAttribution.OFFICIAL:
                official_seconds += net_sec

            if it.end_time is None:
                is_currently_paused = it.is_paused
                current_clock_type = it.clock_type

            interval_breakdown.append({
                "id": it.id,
                "stage_key": it.stage_key,
                "clock_type": it.clock_type,
                "start_time": it.start_time.isoformat() if it.start_time else None,
                "end_time": it.end_time.isoformat() if it.end_time else None,
                "is_active": it.end_time is None,
                "is_paused": it.is_paused,
                "elapsed_seconds": round(net_sec, 1),
                "elapsed_hours": round(net_sec / 3600.0, 2),
                "elapsed_days": round(net_sec / 86400.0, 2),
                "paused_seconds": round(it_pause_sec, 1),
                "rule_version": it.rule_version
            })

        total_elapsed_seconds = institution_seconds + official_seconds

        return {
            "application_id": application_id,
            "rule_version": settings.RULE_VERSION,
            "institution_clock": {
                "total_seconds": round(institution_seconds, 1),
                "total_hours": round(institution_seconds / 3600.0, 2),
                "total_days": round(institution_seconds / 86400.0, 2),
                "percentage": round((institution_seconds / total_elapsed_seconds * 100), 1) if total_elapsed_seconds > 0 else 0
            },
            "official_clock": {
                "total_seconds": round(official_seconds, 1),
                "total_hours": round(official_seconds / 3600.0, 2),
                "total_days": round(official_seconds / 86400.0, 2),
                "percentage": round((official_seconds / total_elapsed_seconds * 100), 1) if total_elapsed_seconds > 0 else 0
            },
            "total_elapsed": {
                "total_seconds": round(total_elapsed_seconds, 1),
                "total_hours": round(total_elapsed_seconds / 3600.0, 2),
                "total_days": round(total_elapsed_seconds / 86400.0, 2)
            },
            "paused_duration": {
                "total_seconds": round(paused_seconds, 1),
                "total_hours": round(paused_seconds / 3600.0, 2)
            },
            "status": {
                "is_active": any(it["is_active"] for it in interval_breakdown),
                "is_paused": is_currently_paused,
                "active_clock_type": current_clock_type
            },
            "explanation": (
                "Dual-Clock engine calculates exact elapsed time split between Institution Response Clock "
                "(time spent waiting on institution submission or clarification response) and Official Processing Clock "
                "(time spent during statutory review by AICTE officers). Authorized clock pauses and public holidays are subtracted."
            ),
            "interval_breakdown": interval_breakdown
        }
