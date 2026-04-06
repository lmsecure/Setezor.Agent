import asyncio
from asyncio.subprocess import PIPE as asyncPIPE



async def create_async_shell_subprocess(command: list[str]):
    return await asyncio.create_subprocess_exec(
        *command,
        stdin=asyncPIPE,
        stdout=asyncPIPE,
        stderr=asyncPIPE
    )