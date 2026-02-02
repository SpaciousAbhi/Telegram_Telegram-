import unittest
import asyncio
from app.database.session import engine, init_db, AsyncSessionLocal
from app.database import crud
from app.database.models import Task, GlobalRule

class TestDatabase(unittest.TestCase):
    async def asyncSetUp(self):
        # Initialize DB (in-memory sqlite by default for tests if not configured otherwise)
        # Note: We are using the session configured in app/database/session.py which defaults to file.
        # Ideally, we'd override for tests, but for this quick check we'll just clean up.
        await init_db()
        self.session = AsyncSessionLocal()

    async def asyncTearDown(self):
        # Clean up
        await self.session.close()
        # In a real scenario, we might drop tables or use a transaction rollback

    def run_async(self, coro):
        return asyncio.run(coro)

    def test_create_and_list_task(self):
        async def test():
            await self.asyncSetUp()
            try:
                task = await crud.create_task(
                    self.session,
                    source="@src",
                    target="@tgt",
                    find_user="@old",
                    replace_user="@new"
                )
                self.assertIsNotNone(task.id)
                self.assertEqual(task.source, "@src")

                tasks = await crud.get_all_tasks(self.session)
                self.assertTrue(any(t.id == task.id for t in tasks))
            finally:
                await self.asyncTearDown()

        self.run_async(test())

    def test_global_rule(self):
        async def test():
            await self.asyncSetUp()
            try:
                rule = await crud.create_global_rule(
                    self.session,
                    rule_type="replace",
                    target_type="user",
                    find_pattern="@banned",
                    replace_with="SKIP_MESSAGE"
                )
                self.assertIsNotNone(rule.id)

                rules = await crud.get_global_rules(self.session)
                self.assertTrue(any(r.id == rule.id for r in rules))
            finally:
                await self.asyncTearDown()

        self.run_async(test())

if __name__ == '__main__':
    unittest.main()
