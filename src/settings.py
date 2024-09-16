import asyncio
import datetime
import gc
import json
import os
import pathlib

import pyhooks

try:
    LOCAL_MODE = (pathlib.Path.cwd() / ".local").exists()
except Exception:
    LOCAL_MODE = False

AGENT_HOME_DIR = pathlib.Path.cwd() if LOCAL_MODE else pathlib.Path("/home/agent")
AGENT_CODE_DIR = (
    pathlib.Path(__file__).parents[1] if LOCAL_MODE else AGENT_HOME_DIR / ".agent_code"
)

HOOKS = pyhooks.Hooks()
INSTRUCTIONS_FILE = AGENT_HOME_DIR / "instructions.txt"
RUN_INFO_FILE = AGENT_CODE_DIR / "run_info.json"


def get_settings():
    return json.loads(RUN_INFO_FILE.read_text())


def get_timestamp():
    return datetime.datetime.now().isoformat()


def get_task_env():
    return {
        k: v
        for k, v in os.environ.items()
        if k == "API_URL"
        or any(
            k.startswith(prefix)
            for prefix in {
                "AGENT_",
                "METR_",
                "RUN_",
                "TASK_",
            }
        )
    } | {"PYHOOKS_DEBUG": os.getenv("PYHOOKS_DEBUG", "false")}


async def async_cleanup():
    import aiohttp

    all_tasks = [
        task for task in asyncio.all_tasks() if task is not asyncio.current_task()
    ]
    if all_tasks:
        await asyncio.wait(all_tasks)
    unclosed_clients: list[aiohttp.ClientSession] = []
    for obj in gc.get_objects():
        if isinstance(obj, aiohttp.ClientSession) and not obj.closed:
            unclosed_clients.append(obj)
    if unclosed_clients:
        await asyncio.gather(*[client.close() for client in unclosed_clients])
