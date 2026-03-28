"""FastAPI application entry point."""

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
from src.infrastructure.rabbitmq.client import RabbitMQClient

settings = AppConfigs.init()

setup_logger(settings.logger.logging_config_file)
logger = get_logger(__name__)


def init_containers() -> DomainContainer:
    """Initialize and wire DI containers for the worker."""
    container = DomainContainer()
    container.config.from_dict(settings.model_dump())
    container.wire(packages=["src.domains"])
    return container


async def _shutdown(rabbitmq_client: RabbitMQClient) -> None:
    """Close all external service connections gracefully.

    Args:
        rabbitmq_client: RabbitMQ client to close.
    """
    await rabbitmq_client.close()
    logger.info("Service is shutting down correctly")


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

    container = init_containers()
    app.state.container = container

    rabbitmq_client = container.infrastructure.rabbitmq_client()

    try:
        yield
    finally:
        await _shutdown(rabbitmq_client)


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
