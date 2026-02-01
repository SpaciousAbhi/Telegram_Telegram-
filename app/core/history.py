import asyncio
import logging
from app.database.db import get_db
from app.database.models import Task
from app.core.engine import process_message

logger = logging.getLogger(__name__)

async def history_worker(client):
    """
    Background task that processes 'History' mode tasks.
    """
    while True:
        try:
            # Find tasks in history mode that are active
            with get_db() as db:
                tasks = db.query(Task).filter(Task.mode == 'history', Task.is_active == True).all()

            if not tasks:
                await asyncio.sleep(10) # Sleep if no work
                continue

            for task in tasks:
                # Process a batch of messages
                try:
                    # Get entity
                    source = await client.get_entity(task.source_id)

                    # Iterate history from last processed ID
                    # reverse=True means we go from old to new (chronological) if we want to catch up
                    # OR we go from new to old (reverse=False).
                    # Usually backfill means "copy everything I missed".
                    # Let's assume we want to copy *forward* from the last checkpoint.

                    last_id = task.last_processed_id

                    # If last_id is 0, user might want all history or just recent.
                    # Default to recent 100 for safety if 0, or logic can be improved.
                    limit = 100 if last_id == 0 else 50
                    min_id = last_id

                    processed_count = 0

                    async for message in client.iter_messages(source, limit=limit, min_id=min_id, reverse=True):
                        # Process
                        await process_message(client, message, task)
                        processed_count += 1

                        # Rate limit protection
                        await asyncio.sleep(2)

                    if processed_count == 0:
                        # We are caught up or stuck. Pause to save resources?
                        # For now, just log.
                        pass

                except Exception as e:
                    logger.error(f"History Worker Error Task {task.id}: {e}")
                    await asyncio.sleep(5)

            await asyncio.sleep(5) # Pace the worker loop

        except Exception as e:
            logger.error(f"Global History Worker Crash: {e}")
            await asyncio.sleep(10)
