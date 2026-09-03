"""Maps a Provider to its adapter instance.

Mock providers always resolve to the MockAdapter. Real providers register a
concrete adapter class by slug via `register_adapter`.
"""

from .mock import MockAdapter

_REAL_ADAPTERS = {}


def register_adapter(slug: str, adapter_cls) -> None:
    _REAL_ADAPTERS[slug] = adapter_cls


def get_adapter(provider):
    if provider.is_mock:
        return MockAdapter(provider)
    adapter_cls = _REAL_ADAPTERS.get(provider.slug)
    if adapter_cls is None:
        raise NotImplementedError(
            f'No real adapter registered for provider "{provider.slug}". '
            f'Register one with register_adapter() or set is_mock=True.'
        )
    return adapter_cls(provider)
