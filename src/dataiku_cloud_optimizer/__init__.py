"""
Dataiku Cloud Optimizer Agent

A Dataiku-driven agent to optimize multi-cloud (AWS, Azure, GCP) and Databricks workloads.
"""

__version__ = "0.1.0"
__author__ = "Dataiku Cloud Optimizer Team"
__email__ = "support@dataiku.com"

from .core import CloudOptimizerAgent
from .providers import AWSProvider, AzureProvider, GCPProvider
from .strategies import CostOptimizationStrategy
from .integrations import DataikuIntegration, DatabricksIntegration

__all__ = [
    "CloudOptimizerAgent",
    "AWSProvider",
    "AzureProvider", 
    "GCPProvider",
    "CostOptimizationStrategy",
    "DataikuIntegration",
    "DatabricksIntegration",
]