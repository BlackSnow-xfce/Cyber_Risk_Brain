from __future__ import annotations

import json

import requests

from application.finding_explanation import (
    FindingExplanationConfigurationError,
    FindingExplanationInvalidOutputError,
    FindingExplanationModelRequest,
    FindingExplanationModelResponse,
    FindingExplanationProviderError,
    FindingExplanationTimeoutError,
)


class OpenAIFindingExplanationModel:
    provider_id = "openai"
    model_id = "gpt-5.6-terra"
    _RESPONSES_URL = "https://api.openai.com/v1/responses"

    def __init__(
        self,
        api_key: str | None,
        timeout_seconds: float,
        session: requests.Session | None = None,
    ) -> None:
        self._api_key = api_key
        self._timeout_seconds = timeout_seconds
        self._session = session or requests.Session()

    @classmethod
    def from_settings(cls) -> OpenAIFindingExplanationModel:
        import settings

        try:
            timeout = float(settings.OPENAI_EXPLANATION_TIMEOUT_SECONDS)
        except (TypeError, ValueError):
            timeout = 0.0
        return cls(settings.OPENAI_API_KEY, timeout)

    def generate(
        self,
        request: FindingExplanationModelRequest,
    ) -> FindingExplanationModelResponse:
        if self._api_key is None or not self._api_key.strip():
            raise FindingExplanationConfigurationError(
                "OPENAI_API_KEY is not configured."
            )
        if self._timeout_seconds <= 0:
            raise FindingExplanationConfigurationError(
                "OpenAI explanation timeout is invalid."
            )

        payload = {
            "model": self.model_id,
            "input": [
                {
                    "role": "developer",
                    "content": request.instructions,
                },
                {
                    "role": "user",
                    "content": request.untrusted_data_json,
                },
            ],
            "text": {
                "format": {
                    "type": "json_schema",
                    "name": "finding_explanation",
                    "strict": True,
                    "schema": request.output_schema,
                }
            },
        }

        try:
            response = self._session.post(
                self._RESPONSES_URL,
                headers={
                    "Authorization": f"Bearer {self._api_key}",
                    "Content-Type": "application/json",
                },
                json=payload,
                timeout=self._timeout_seconds,
            )
        except requests.Timeout:
            raise FindingExplanationTimeoutError(
                "OpenAI explanation request timed out."
            ) from None
        except requests.RequestException:
            raise FindingExplanationProviderError(
                "OpenAI explanation request failed."
            ) from None

        if not 200 <= response.status_code < 300:
            raise FindingExplanationProviderError(
                "OpenAI explanation provider returned an error."
            )

        try:
            response_data = response.json()
        except (ValueError, json.JSONDecodeError):
            raise FindingExplanationInvalidOutputError(
                "OpenAI explanation response is invalid."
            ) from None

        output_text = self._extract_output_text(response_data)
        try:
            structured_output = json.loads(output_text)
        except json.JSONDecodeError:
            raise FindingExplanationInvalidOutputError(
                "OpenAI explanation output is not valid JSON."
            ) from None

        return FindingExplanationModelResponse(
            provider_id=self.provider_id,
            model_id=self.model_id,
            output=structured_output,
        )

    @staticmethod
    def _extract_output_text(response_data: object) -> str:
        if not isinstance(response_data, dict):
            raise FindingExplanationInvalidOutputError(
                "OpenAI explanation response is invalid."
            )
        output = response_data.get("output")
        if not isinstance(output, list):
            raise FindingExplanationInvalidOutputError(
                "OpenAI explanation response has no output."
            )
        for item in output:
            if not isinstance(item, dict) or item.get("type") != "message":
                continue
            content = item.get("content")
            if not isinstance(content, list):
                continue
            for content_item in content:
                if (
                    isinstance(content_item, dict)
                    and content_item.get("type") == "output_text"
                ):
                    text = content_item.get("text")
                    if isinstance(text, str) and text.strip():
                        return text
        raise FindingExplanationInvalidOutputError(
            "OpenAI explanation response has no output text."
        )
