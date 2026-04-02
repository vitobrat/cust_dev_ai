"""FastAPI application entry point.
claude --resume 6b17804a-5368-4558-90e1-9fd87563c371
(редис клиент)"""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

import uvicorn
from fastapi import APIRouter, FastAPI
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from src.configs.config import AppConfigs
from src.configs.log.logger import get_logger, setup_logger
from src.domains.interview.app.requests.router import router as interview_router
from src.domains.persona.app.requests.router import router as persona_router
from src.domains.sub_interview.app.requests.router import (
    router as sub_interview_router,
)
from src.domains.task.app.requests.router import router as task_router
from src.domains.user.app.requests.router import router as user_router
from src.infrastructure.containers.domain import DomainContainer
from src.infrastructure.db.postgres.client import DatabaseClient
from src.infrastructure.db.redis.client import RedisClient

settings = AppConfigs.init()

setup_logger(settings.logger.logging_config_file)
logger = get_logger(__name__)


async def lifespan_shut_down(redis: RedisClient, postgres: DatabaseClient) -> None:
    logger.info("Service is shutting down correctly")
    await postgres.dispose()
    await redis.close()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Manage application startup and shutdown lifecycle.

    Initializes the DI container, wires all domain packages on startup,
    and logs a shutdown message on teardown.

    Args:
        app: The FastAPI application instance.

    Yields:
        Control back to the framework while the application is running.
    """
    logger.info("Cust-dev llm service is starting up...")

    container = DomainContainer()
    container.config.from_dict(settings.model_dump())
    container.wire(packages=["src.domains"])
    app.state.container = container

    redis = container.infrastructure.redis_client()  # type: ignore[operator]
    postgres = container.infrastructure.db_client()  # type: ignore[operator]

    try:
        yield
    finally:
        await lifespan_shut_down(redis, postgres)


limiter = Limiter(key_func=get_remote_address)

api_v1_router = APIRouter(prefix="/api/v1")
api_v1_router.include_router(interview_router)
api_v1_router.include_router(persona_router)
api_v1_router.include_router(sub_interview_router)
api_v1_router.include_router(task_router)
api_v1_router.include_router(user_router)

app = FastAPI(lifespan=lifespan)
app.include_router(api_v1_router)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


if __name__ == "__main__":
    uvicorn.run(
        "src.app:app",
        host=settings.app_host,
        port=settings.app_port,
        log_level=settings.log_level.value.lower(),
        workers=settings.workers_number,
    )
