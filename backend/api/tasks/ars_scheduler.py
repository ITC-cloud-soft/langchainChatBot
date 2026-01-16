"""
ARS Scheduler Module

This module provides scheduled tasks for updating system prompts from ARS API.
"""

import asyncio
import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from datetime import datetime

from api.services.ars_service import ArsService

logger = logging.getLogger(__name__)


class ArsScheduler:
    """Scheduler for ARS-related tasks"""
    
    def __init__(self):
        self.scheduler = AsyncIOScheduler()
        self._running = False
    
    def start(self, update_interval_minutes: int = 30):
        """
        Start the ARS scheduler
        
        Args:
            update_interval_minutes: Interval in minutes to update system prompts (default: 30)
        """
        if self._running:
            logger.warning("ARS scheduler is already running")
            return
        
        logger.info(f"Starting ARS scheduler with {update_interval_minutes} minute interval")
        
        # Add job to update system prompts
        self.scheduler.add_job(
            self._update_system_prompts_job,
            trigger=IntervalTrigger(minutes=update_interval_minutes),
            id='update_ars_system_prompts',
            name='Update ARS System Prompts',
            replace_existing=True
        )
        
        # Start the scheduler
        self.scheduler.start()
        self._running = True
        
        logger.info("ARS scheduler started successfully")
    
    def stop(self):
        """Stop the ARS scheduler"""
        if not self._running:
            return
        
        logger.info("Stopping ARS scheduler")
        self.scheduler.shutdown()
        self._running = False
        logger.info("ARS scheduler stopped")
    
    async def _update_system_prompts_job(self):
        """Job to update system prompts from ARS"""
        try:
            logger.info("Starting scheduled ARS system prompt update")
            start_time = datetime.now()
            
            await ArsService.update_all_system_prompts()
            
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            logger.info(f"ARS system prompt update completed in {duration:.2f} seconds")
            
        except Exception as e:
            logger.error(f"Error in ARS system prompt update job: {str(e)}", exc_info=True)
    
    async def trigger_update_now(self):
        """Manually trigger an immediate update of system prompts"""
        logger.info("Manually triggering ARS system prompt update")
        await self._update_system_prompts_job()


# Global scheduler instance
_ars_scheduler = None


def get_ars_scheduler() -> ArsScheduler:
    """Get the global ARS scheduler instance"""
    global _ars_scheduler
    if _ars_scheduler is None:
        _ars_scheduler = ArsScheduler()
    return _ars_scheduler


def start_ars_scheduler(update_interval_minutes: int = 30):
    """Start the global ARS scheduler"""
    scheduler = get_ars_scheduler()
    scheduler.start(update_interval_minutes)


def stop_ars_scheduler():
    """Stop the global ARS scheduler"""
    scheduler = get_ars_scheduler()
    scheduler.stop()
