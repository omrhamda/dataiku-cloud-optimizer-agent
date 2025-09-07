"""
Configuration management utilities
"""

import yaml
import json
from pathlib import Path
from typing import Dict, Any, Union


def load_config(config_path: Union[str, Path]) -> Dict[str, Any]:
    """
    Load configuration from YAML or JSON file
    
    Args:
        config_path: Path to configuration file
        
    Returns:
        Dictionary containing configuration data
        
    Raises:
        FileNotFoundError: If config file doesn't exist
        ValueError: If config file format is unsupported
    """
    config_path = Path(config_path)
    
    if not config_path.exists():
        raise FileNotFoundError(f"Configuration file not found: {config_path}")
    
    with open(config_path, 'r') as f:
        if config_path.suffix.lower() in ['.yaml', '.yml']:
            return yaml.safe_load(f) or {}
        elif config_path.suffix.lower() == '.json':
            return json.load(f)
        else:
            raise ValueError(f"Unsupported config file format: {config_path.suffix}")


def save_config(config: Dict[str, Any], config_path: Union[str, Path]) -> None:
    """
    Save configuration to YAML or JSON file
    
    Args:
        config: Configuration dictionary to save
        config_path: Path where to save the configuration
    """
    config_path = Path(config_path)
    
    # Create parent directories if they don't exist
    config_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(config_path, 'w') as f:
        if config_path.suffix.lower() in ['.yaml', '.yml']:
            yaml.dump(config, f, default_flow_style=False, indent=2)
        elif config_path.suffix.lower() == '.json':
            json.dump(config, f, indent=2)
        else:
            raise ValueError(f"Unsupported config file format: {config_path.suffix}")


def get_default_config() -> Dict[str, Any]:
    """Get default configuration template"""
    return {
        "providers": {
            "aws": {
                "region": "us-east-1",
                "profile": "default"
            },
            "azure": {
                "subscription_id": "",
                "tenant_id": ""
            },
            "gcp": {
                "project_id": "",
                "credentials_path": ""
            }
        },
        "integrations": {
            "dataiku": {
                "url": "",
                "api_key": "",
                "project_key": ""
            },
            "databricks": {
                "workspace_url": "",
                "token": "",
                "cluster_id": ""
            }
        },
        "optimization": {
            "strategies": ["cost_optimization"],
            "thresholds": {
                "min_savings_percent": 10.0,
                "min_confidence_score": 0.7
            },
            "schedule": {
                "analysis_frequency": "daily",
                "report_frequency": "weekly"
            }
        },
        "logging": {
            "level": "INFO",
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        }
    }


def validate_config(config: Dict[str, Any]) -> tuple[bool, list[str]]:
    """
    Validate configuration structure and required fields
    
    Args:
        config: Configuration dictionary to validate
        
    Returns:
        Tuple of (is_valid, list_of_errors)
    """
    errors = []
    
    # Check required top-level sections
    required_sections = ["providers", "integrations", "optimization"]
    for section in required_sections:
        if section not in config:
            errors.append(f"Missing required section: {section}")
    
    # Validate providers section
    if "providers" in config:
        providers = config["providers"]
        for provider_name in ["aws", "azure", "gcp"]:
            if provider_name in providers:
                provider_config = providers[provider_name]
                if provider_name == "aws":
                    if "region" not in provider_config:
                        errors.append("AWS provider missing 'region' field")
                elif provider_name == "azure":
                    if "subscription_id" not in provider_config:
                        errors.append("Azure provider missing 'subscription_id' field")
                elif provider_name == "gcp":
                    if "project_id" not in provider_config:
                        errors.append("GCP provider missing 'project_id' field")
    
    # Validate integrations section
    if "integrations" in config:
        integrations = config["integrations"]
        if "dataiku" in integrations:
            dataiku_config = integrations["dataiku"]
            required_fields = ["url", "api_key"]
            for field in required_fields:
                if field not in dataiku_config or not dataiku_config[field]:
                    errors.append(f"Dataiku integration missing required field: {field}")
        
        if "databricks" in integrations:
            databricks_config = integrations["databricks"]
            required_fields = ["workspace_url", "token"]
            for field in required_fields:
                if field not in databricks_config or not databricks_config[field]:
                    errors.append(f"Databricks integration missing required field: {field}")
    
    # Validate optimization section
    if "optimization" in config:
        optimization = config["optimization"]
        if "thresholds" in optimization:
            thresholds = optimization["thresholds"]
            if "min_savings_percent" in thresholds:
                try:
                    min_savings = float(thresholds["min_savings_percent"])
                    if min_savings < 0 or min_savings > 100:
                        errors.append("min_savings_percent must be between 0 and 100")
                except (ValueError, TypeError):
                    errors.append("min_savings_percent must be a number")
            
            if "min_confidence_score" in thresholds:
                try:
                    min_confidence = float(thresholds["min_confidence_score"])
                    if min_confidence < 0 or min_confidence > 1:
                        errors.append("min_confidence_score must be between 0 and 1")
                except (ValueError, TypeError):
                    errors.append("min_confidence_score must be a number")
    
    return len(errors) == 0, errors


def merge_configs(base_config: Dict[str, Any], override_config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Merge two configuration dictionaries, with override values taking precedence
    
    Args:
        base_config: Base configuration dictionary
        override_config: Override configuration dictionary
        
    Returns:
        Merged configuration dictionary
    """
    def _merge_dicts(base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
        result = base.copy()
        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = _merge_dicts(result[key], value)
            else:
                result[key] = value
        return result
    
    return _merge_dicts(base_config, override_config)