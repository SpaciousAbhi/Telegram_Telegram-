from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import delete
from .models import Task, GlobalRule

# --- Tasks ---

async def create_task(db: AsyncSession, source: str, target: str,
                      find_user: str = None, replace_user: str = None,
                      find_link: str = None, replace_link: str = None):
    new_task = Task(
        source=source,
        target=target,
        find_user=find_user,
        replace_user=replace_user,
        find_link=find_link,
        replace_link=replace_link
    )
    db.add(new_task)
    await db.commit()
    await db.refresh(new_task)
    return new_task

async def get_all_tasks(db: AsyncSession):
    result = await db.execute(select(Task))
    return result.scalars().all()

async def delete_task(db: AsyncSession, task_id: int):
    # Using delete statement directly
    await db.execute(delete(Task).where(Task.id == task_id))
    await db.commit()
    return True # Simplified for now

async def update_task_ids(db: AsyncSession, task_id: int, source_id: int = None, target_id: int = None):
    result = await db.execute(select(Task).where(Task.id == task_id))
    task = result.scalars().first()
    if task:
        if source_id: task.source_id = source_id
        if target_id: task.target_id = target_id
        await db.commit()
        await db.refresh(task)
    return task

# --- Global Rules ---

async def create_global_rule(db: AsyncSession, rule_type: str, target_type: str,
                             find_pattern: str, replace_with: str = None):
    rule = GlobalRule(
        rule_type=rule_type,
        target_type=target_type,
        find_pattern=find_pattern,
        replace_with=replace_with
    )
    db.add(rule)
    await db.commit()
    await db.refresh(rule)
    return rule

async def get_global_rules(db: AsyncSession):
    result = await db.execute(select(GlobalRule))
    return result.scalars().all()
