"""System endpoints — health check, shutdown."""

import asyncio
import logging
import os

from fastapi import APIRouter

router = APIRouter(tags=["system"])
logger = logging.getLogger(__name__)


@router.post("/api/system/shutdown")
async def system_shutdown():
    """Gracefully shut down the server."""
    logger.info("Shutdown requested, exiting in 500ms")

    async def _exit_soon():
        await asyncio.sleep(0.5)
        os._exit(0)

    asyncio.get_event_loop().create_task(_exit_soon())
    return {"status": "shutting_down", "killed": []}
