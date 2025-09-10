"""Unit tests for configuration utilities"""

import json
import tempfile
from pathlib import Path

import pytest
import yaml

from dataiku_cloud_optimizer.utils.config import (
    get_default_config,
    load_config,
    merge_configs,
    save_config,
    validate_config,
)


class TestConfigUtils:
    """Test cases for configuration utilities"""

    def test_load_config_yaml(self):
        """Test loading YAML configuration"""
        config_data = {"providers": {"aws": {"region": "us-east-1"}}}

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            yaml.dump(config_data, f)
            config_path = f.name

        try:
            result = load_config(config_path)
            assert result == config_data
        finally:
            Path(config_path).unlink()

    def test_load_config_json(self):
        """Test loading JSON configuration"""
        config_data = {"providers": {"aws": {"region": "us-east-1"}}}

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(config_data, f)
            config_path = f.name

        try:
            result = load_config(config_path)
            assert result == config_data
        finally:
            Path(config_path).unlink()

    def test_load_config_nonexistent(self):
        """Test loading nonexistent configuration file"""
        with pytest.raises(FileNotFoundError):
            load_config("/nonexistent/path/config.yaml")

    def test_load_config_unsupported_format(self):
        """Test loading unsupported configuration format"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write("some text")
            config_path = f.name

        try:
            with pytest.raises(ValueError, match="Unsupported config file format"):
                load_config(config_path)
        finally:
            Path(config_path).unlink()

    def test_save_config_yaml(self):
        """Test saving YAML configuration"""
        config_data = {"providers": {"aws": {"region": "us-east-1"}}}

        with tempfile.NamedTemporaryFile(suffix=".yaml", delete=False) as f:
            config_path = f.name

        try:
            save_config(config_data, config_path)

            # Verify file was created and content is correct
            with open(config_path) as f:
                loaded_data = yaml.safe_load(f)

            assert loaded_data == config_data
        finally:
            Path(config_path).unlink()

    def test_save_config_json(self):
        """Test saving JSON configuration"""
        config_data = {"providers": {"aws": {"region": "us-east-1"}}}

        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            config_path = f.name

        try:
            save_config(config_data, config_path)

            # Verify file was created and content is correct
            with open(config_path) as f:
                loaded_data = json.load(f)

            assert loaded_data == config_data
        finally:
            Path(config_path).unlink()

    def test_get_default_config(self):
        """Test getting default configuration"""
        config = get_default_config()

        assert "providers" in config
        assert "integrations" in config
        assert "optimization" in config
        assert "logging" in config

        # Check provider structure
        assert "aws" in config["providers"]
        assert "azure" in config["providers"]
        assert "gcp" in config["providers"]

        # Check integration structure
        assert "dataiku" in config["integrations"]
        assert "databricks" in config["integrations"]

    def test_validate_config_valid(self):
        """Test validation of valid configuration"""
        config = get_default_config()
        config["providers"]["aws"]["region"] = "us-east-1"
        config["integrations"]["dataiku"]["url"] = "https://test.com"
        config["integrations"]["dataiku"]["api_key"] = "test-key"
        config["integrations"]["databricks"]["workspace_url"] = (
            "https://test.databricks.com"
        )
        config["integrations"]["databricks"]["token"] = "test-token"

        is_valid, errors = validate_config(config)

        if not is_valid:
            print(f"Validation errors: {errors}")

        assert is_valid
        assert len(errors) == 0

    def test_validate_config_missing_sections(self):
        """Test validation of configuration with missing sections"""
        config = {"providers": {}}  # Missing integrations and optimization

        is_valid, errors = validate_config(config)

        assert not is_valid
        assert "Missing required section: integrations" in errors
        assert "Missing required section: optimization" in errors

    def test_validate_config_invalid_thresholds(self):
        """Test validation of configuration with invalid thresholds"""
        config = get_default_config()
        config["optimization"]["thresholds"]["min_savings_percent"] = 150  # Invalid
        config["optimization"]["thresholds"]["min_confidence_score"] = 1.5  # Invalid

        is_valid, errors = validate_config(config)

        assert not is_valid
        assert "min_savings_percent must be between 0 and 100" in errors
        assert "min_confidence_score must be between 0 and 1" in errors

    def test_merge_configs_simple(self):
        """Test merging simple configurations"""
        base_config = {"a": 1, "b": 2}
        override_config = {"b": 3, "c": 4}

        result = merge_configs(base_config, override_config)

        expected = {
            "a": 1,
            "b": 3,  # Override value
            "c": 4,
        }
        assert result == expected

    def test_merge_configs_nested(self):
        """Test merging nested configurations"""
        base_config = {
            "providers": {
                "aws": {"region": "us-east-1", "profile": "default"},
                "azure": {"subscription_id": "base-sub"},
            }
        }
        override_config = {
            "providers": {
                "aws": {"profile": "prod"},  # Override profile only
                "gcp": {"project_id": "test-project"},  # New provider
            }
        }

        result = merge_configs(base_config, override_config)

        expected = {
            "providers": {
                "aws": {"region": "us-east-1", "profile": "prod"},
                "azure": {"subscription_id": "base-sub"},
                "gcp": {"project_id": "test-project"},
            }
        }
        assert result == expected

    def test_merge_configs_preserve_original(self):
        """Test that merge operation preserves original configurations"""
        base_config = {"a": 1, "b": 2}
        override_config = {"b": 3, "c": 4}

        original_base = base_config.copy()
        original_override = override_config.copy()

        merge_configs(base_config, override_config)

        # Original configs should be unchanged
        assert base_config == original_base
        assert override_config == original_override
