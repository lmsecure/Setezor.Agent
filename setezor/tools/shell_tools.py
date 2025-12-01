import asyncio
from asyncio.subprocess import PIPE as asyncPIPE
from setezor.settings import PLATFORM



async def create_async_shell_subprocess(command: list[str]):
    if PLATFORM == "Windows":
        return await asyncio.create_subprocess_exec(
            *command,
            stdin=asyncPIPE,
            stdout=asyncPIPE,
            stderr=asyncPIPE
        )
    else:
        return await asyncio.create_subprocess_shell(
            ' '.join(command),
            stdin=asyncPIPE,
            stdout=asyncPIPE,
            stderr=asyncPIPE
        )