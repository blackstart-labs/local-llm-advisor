"""Model registry interface and query provider."""

from __future__ import annotations

from abc import ABC, abstractmethod

from llm_advisor.models.catalog import get_default_catalog
from llm_advisor.models.schema import ModelProfile


class ModelRegistry(ABC):
    """Abstract interface for querying LLM profiles."""

    @abstractmethod
    def list_all(self) -> list[ModelProfile]:
        """Return list of all registered models."""
        pass

    @abstractmethod
    def get_by_id(self, model_id: str) -> ModelProfile | None:
        """Fetch specific model profile by unique ID."""
        pass

    @abstractmethod
    def filter_by_use_case(self, use_case: str) -> list[ModelProfile]:
        """Filter models matching a given use case tag."""
        pass

    @abstractmethod
    def filter_by_max_parameters(self, max_params_billions: float) -> list[ModelProfile]:
        """Filter models having parameters <= threshold."""
        pass


class DefaultModelRegistry(ModelRegistry):
    """In-memory model registry loaded from static catalog dataset."""

    def __init__(self, models: list[ModelProfile] | None = None) -> None:
        self._models = models if models is not None else get_default_catalog()

    def list_all(self) -> list[ModelProfile]:
        return list(self._models)

    def get_by_id(self, model_id: str) -> ModelProfile | None:
        target = model_id.lower().strip()
        for m in self._models:
            if m.id.lower() == target or m.name.lower() == target:
                return m
        return None

    def filter_by_use_case(self, use_case: str) -> list[ModelProfile]:
        target = use_case.lower().strip()
        return [m for m in self._models if target in [u.lower() for u in m.use_cases]]

    def filter_by_max_parameters(self, max_params_billions: float) -> list[ModelProfile]:
        return [m for m in self._models if m.parameter_count_billions <= max_params_billions]
