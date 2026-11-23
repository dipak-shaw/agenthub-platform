"""Select the offline model unless a real endpoint and deployment are configured."""

from pydantic_ai.models import Model

from agent_hub.core.models.demo import demo_model
from agent_hub.core.models.foundry import FoundryModel, foundry_model
from agent_hub.core.models.retry import RetryModel
from agent_hub.core.settings import Settings


def build_model(settings: Settings, deployment: str = "default") -> Model:
    if settings.is_demo(deployment):
        return demo_model()
    return RetryModel(foundry_model(settings, deployment))


async def close_model(model: Model) -> None:
    underlying = model.wrapped if isinstance(model, RetryModel) else model
    if isinstance(underlying, FoundryModel):
        await underlying.close()
