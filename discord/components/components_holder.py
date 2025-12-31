from __future__ import annotations

from typing import Generic, cast

from typing_extensions import TypeVarTuple, Unpack, override

from .component import Component, WalkableComponentMixin
from .partial_components import PartialComponent, PartialWalkableComponentMixin
from .type_aliases import AnyComponent, AnyPartialComponent

Ts = TypeVarTuple(
    "Ts", default=Unpack[tuple[AnyComponent | AnyPartialComponent]]
)  # Unforntunately, we cannot use `TypeVarTuple` with upper bounds yet.


class ComponentsHolder(tuple[Unpack[Ts]], Generic[Unpack[Ts]]):
    """A sequence of components that can be used in Discord Bot UI Kit.

    This holder that is used to represent a collection of components, notably in a message.

    .. versionadded:: 3.0
    """

    __slots__: tuple[str, ...] = ()

    def __new__(cls, *components: Unpack[Ts]) -> ComponentsHolder[Unpack[Ts]]:
        return super().__new__(cls, components)

    def get_by_id(self, component_id: str | int) -> AnyComponent | AnyPartialComponent | None:
        """Get a component by its custom ID."""
        for maybe_component in self:
            if not isinstance(maybe_component, (Component, PartialComponent)):
                raise TypeError(f"Expected {Component} or {PartialComponent} but got {maybe_component}")
            component = cast(AnyComponent | AnyPartialComponent, maybe_component)
            if isinstance(component_id, str) and getattr(component, "custom_id", None) == component_id:
                return component
            elif isinstance(component_id, int) and getattr(component, "id", None) == component_id:
                return component

            if isinstance(component, (WalkableComponentMixin, PartialWalkableComponentMixin)):
                if found := component.get_by_id(component_id):
                    return found
        return None

    @override
    def __repr__(self) -> str:
        return f"<ComponentsHolder components={super().__repr__()}>"
