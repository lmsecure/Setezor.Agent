import os
import asyncio



class WatchDog:

    def __init__(self, info_manager, path: str):
        self.info_manager = info_manager
        self.path = path
        self.count_files = self.get_count_files()
        self._task = asyncio.create_task(self.run())

    def get_count_files(self) -> int:
        return len(os.listdir(self.path))

    async def run(self):
        try:
            while True:
                new_count_files = self.get_count_files()
                if new_count_files != self.count_files:
                    await self.info_manager.send_info()
                self.count_files = new_count_files
                await asyncio.sleep(1)
        except Exception as e:
            self._task.cancel()
