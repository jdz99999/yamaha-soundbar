"""Base coordinator entity for Yamaha integration."""

from __future__ import annotations

from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .coordinator import YamahaCoordinator


class YamahaCoordinatorEntity(CoordinatorEntity[YamahaCoordinator]):
    """Base class for entities backed by YamahaCoordinator."""

    _attr_has_entity_name = True

    def __init__(self, coordinator: YamahaCoordinator) -> None:
        super().__init__(coordinator)
