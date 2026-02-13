from dependency_injector import containers, providers

from src.configs.config import AppConfigs
from src.infrastructure.containers.domain import DomainContainer
from src.infrastructure.containers.infrastructure import InfrastructureContainer


class RootContainer(containers.DeclarativeContainer):
    config: AppConfigs = providers.Configuration()

    infrastructure: InfrastructureContainer = providers.Container(
        InfrastructureContainer,
        config=config,
    )

    domain: DomainContainer = providers.Container(
        DomainContainer,
        infrastructure=infrastructure,
    )
