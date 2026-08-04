import pytest
from datetime import date
from taxos.application.updater.versioning import VersioningService
from taxos.application.updater.coordinator import UpdateCoordinator
from taxos.plugins.updater.base import PluginUpdateResult
from taxos.infrastructure.database.models.updater import TaxRuleVersion, TaxUpdateJob

pytestmark = pytest.mark.asyncio


async def test_versioning_service_applies_new_update(session):
    service = VersioningService(session)
    
    update = PluginUpdateResult(
        jurisdiction="US",
        tax_year=2025,
        rule_payload={"test": "data"},
        effective_from=date(2025, 1, 1)
    )
    
    # First application should succeed and create a new version
    applied = await service.apply_update(update)
    assert applied is True
    
    # Second application of the exact same payload should be skipped
    applied_again = await service.apply_update(update)
    assert applied_again is False


async def test_versioning_service_rollback(session):
    service = VersioningService(session)
    
    update1 = PluginUpdateResult(
        jurisdiction="US",
        tax_year=2025,
        rule_payload={"test": "version1"}
    )
    update2 = PluginUpdateResult(
        jurisdiction="US",
        tax_year=2025,
        rule_payload={"test": "version2"}
    )
    
    await service.apply_update(update1)
    await service.apply_update(update2)
    
    # Get active version
    active = await service._get_active_version("US", 2025)
    assert active is not None
    assert active.version_hash == service._hash_payload({"test": "version2"})
    
    # Rollback to version1
    v1_hash = service._hash_payload({"test": "version1"})
    success = await service.rollback(v1_hash)
    assert success is True
    
    # Verify active is now version1
    new_active = await service._get_active_version("US", 2025)
    assert new_active.version_hash == v1_hash


async def test_update_coordinator(engine, session):
    coordinator = UpdateCoordinator(engine)
    
    # Run cycle
    updates = await coordinator.run_update_cycle(2025)
    assert updates == 1  # The US mock plugin returns 1 new rule
    
    # Run again, should be 0 because hash hasn't changed
    updates_again = await coordinator.run_update_cycle(2025)
    assert updates_again == 0
