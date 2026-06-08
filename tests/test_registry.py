from unittest.mock import patch

import pytest

from geosearch.registry import TableNotFoundException, get_registry


@pytest.mark.django_db
def test_registry_skips_table_without_geometry(dataset, dataset_registry):
    with pytest.raises(TableNotFoundException):
        dataset_registry.get_table_by_path("dataset/table_without_geometry")


@pytest.mark.django_db
def test_registry_caches_tables_for_scope(dataset, dataset_registry):
    # Get tables for a scope, this should populate the cache
    tables_for_scope = dataset_registry.get_table_paths(frozenset(["scope1"]))

    # The cache should now have an entry for the scopes
    assert frozenset(["scope1"]) in dataset_registry._tables_for_scopes

    # Request the tables again to validate cached object is returned
    tables_for_scope_again = dataset_registry.get_table_paths(frozenset(["scope1"]))
    assert id(tables_for_scope_again) == id(tables_for_scope)


@pytest.mark.django_db
@patch("geosearch.registry.DatasetRegistry.initialize")
def test_registry_initialized_once(mock_initialize, dataset):
    mock_registery = get_registry()
    # Set initialized to true to mimic the state after initialization
    mock_registery.is_initialized = True

    # Call the registry again and assert initialize is only called once
    get_registry()
    mock_initialize.assert_called_once()
