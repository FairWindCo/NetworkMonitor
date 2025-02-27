# https://pypi.org/project/icmplib/
# pip3 install icmplib
import asyncio


class AsyncScheduler:
    def __init__(self):
        self.second_task = None
        self.minute_task = None
        self.running = True

    async def seconds_function(self, *args, **kwargs):
        print('second')

    async def minutes_function(self, *args, **kwargs):
        print('minute')

    async def timed_tasks(self, interval, func, *args, **kwargs):
        while self.running:
            asyncio.create_task(func(*args, **kwargs))
            try:
                await asyncio.sleep(interval)
            except asyncio.CancelledError:
                self.running = False
                self.minute_task.cancel()
                self.second_task.cancel()
                break

    def create_seconds_task(self):
        return asyncio.create_task(self.timed_tasks(1, self.seconds_function))

    def create_minutes_task(self):
        return asyncio.create_task(self.timed_tasks(60, self.minutes_function))

    async def main(self):
        print('main: create schedule tasks')
        self.minute_task = self.create_minutes_task()
        self.second_task = self.create_seconds_task()
        try:
            await self.second_task
            await self.minute_task
        except asyncio.CancelledError:
            self.running = False


    def stop(self):
        self.running = False
        self.minute_task.cancel()
        self.second_task.cancel()

    def execute(self):
        asyncio.run(self.main())


if __name__ == '__main__':
    AsyncScheduler().execute()