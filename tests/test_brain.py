import unittest
import asyncio
from app.core.brain import JulesBrain
from app.database.session import init_db, AsyncSessionLocal

class TestJulesBrain(unittest.TestCase):
    async def asyncSetUp(self):
        await init_db()
        self.brain = JulesBrain()
        self.session = AsyncSessionLocal()

    async def asyncTearDown(self):
        await self.session.close()

    def run_async(self, coro):
        return asyncio.run(coro)

    def test_add_task_command(self):
        async def test():
            await self.asyncSetUp()
            try:
                cmd = "/add\nsource: @test_src\ntarget: @test_tgt"
                response = await self.brain.process_text(cmd)
                self.assertIn("✅ Task added", response)

                # Verify in DB
                response_list = await self.brain.process_text("/list")
                self.assertIn("@test_src", response_list)
            finally:
                await self.asyncTearDown()
        self.run_async(test())

    def test_unknown_command(self):
        async def test():
            await self.asyncSetUp()
            response = await self.brain.process_text("hello world")
            self.assertIn("I didn't understand", response)
            await self.asyncTearDown()
        self.run_async(test())

if __name__ == '__main__':
    unittest.main()
