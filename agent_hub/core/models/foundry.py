"""Azure chat completions using the installed PydanticAI Azure provider."""

from typing import Any

from openai import AsyncAzureOpenAI
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.azure import AzureProvider

from agent_hub.core.errors import ErrorCode, HubError
from agent_hub.core.settings import Settings


class FoundryModel(OpenAIChatModel):
    """Own the HTTP client and optional credential for explicit shutdown."""

    def __init__(self, deployment: str, client: AsyncAzureOpenAI, credential: Any = None) -> None:
        super().__init__(deployment, provider=AzureProvider(openai_client=client))
        self.azure_client = client
        self.credential = credential

    async def close(self) -> None:
        await self.azure_client.close()
        if self.credential is not None:
            await self.credential.close()


def foundry_model(settings: Settings, deployment: str) -> FoundryModel:
    selected = settings.azure_foundry_deployment if deployment == "default" else deployment
    credential = None
    if settings.azure_foundry_auth == "entra_id":
        try:
            from azure.identity.aio import DefaultAzureCredential, get_bearer_token_provider
        except ImportError as exc:
            raise HubError(
                ErrorCode.MODEL_UNAVAILABLE, "Install the entra extra for Entra ID"
            ) from exc
        credential = DefaultAzureCredential()
        token_provider = get_bearer_token_provider(
            credential, "https://cognitiveservices.azure.com/.default"
        )
        client = AsyncAzureOpenAI(
            azure_endpoint=settings.azure_foundry_endpoint,
            api_version=settings.azure_foundry_api_version,
            azure_ad_token_provider=token_provider,
            max_retries=0,
        )
    else:
        key = settings.azure_foundry_api_key.get_secret_value()
        if not key:
            raise HubError(ErrorCode.MODEL_UNAVAILABLE, "Foundry API key is missing")
        client = AsyncAzureOpenAI(
            azure_endpoint=settings.azure_foundry_endpoint,
            api_version=settings.azure_foundry_api_version,
            api_key=key,
            max_retries=0,
        )
    return FoundryModel(selected, client, credential)
