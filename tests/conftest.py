"""
Test configuration and fixtures
"""

import pytest


@pytest.fixture
def sample_aws_config():
    """Sample AWS configuration for testing"""
    return {"region": "us-east-1", "profile": "test"}


@pytest.fixture
def sample_azure_config():
    """Sample Azure configuration for testing"""
    return {"subscription_id": "test-subscription-id", "tenant_id": "test-tenant-id"}


@pytest.fixture
def sample_gcp_config():
    """Sample GCP configuration for testing"""
    return {
        "project_id": "test-project",
        "credentials_path": "/path/to/credentials.json",
    }


@pytest.fixture
def sample_cost_data():
    """Sample cost data for testing optimization strategies"""
    return {
        "provider": "aws",
        "total_cost": 1000.0,
        "resource_count": 50,
        "period": "2024-11-01 to 2024-12-01",
        "services": {"EC2": 600.0, "RDS": 250.0, "S3": 150.0},
        "regions": {"us-east-1": 700.0, "us-west-2": 300.0},
    }


@pytest.fixture
def sample_dataiku_config():
    """Sample Dataiku configuration for testing"""
    return {
        "url": "https://test-dataiku.com",
        "api_key": "test-api-key",
        "project_key": "TEST_PROJECT",
    }


@pytest.fixture
def sample_databricks_config():
    """Sample Databricks configuration for testing"""
    return {
        "workspace_url": "https://test-workspace.cloud.databricks.com",
        "token": "test-token",
        "cluster_id": "test-cluster-id",
    }
