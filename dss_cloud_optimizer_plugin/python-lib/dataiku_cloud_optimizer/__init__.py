"""Embedded subset of Dataiku Cloud Optimizer for DSS plugin."""
from .core import CloudOptimizerAgent, OptimizationResult
from .providers.aws import AWSProvider
from .providers.azure import AzureProvider
from .providers.gcp import GCPProvider
from .strategies.cost_optimization import CostOptimizationStrategy
from .llm import SimpleLLM
from .notify import SlackNotifier, EmailNotifier

__all__ = [
    "CloudOptimizerAgent",
    "OptimizationResult",
    "AWSProvider",
    "AzureProvider",
    "GCPProvider",
    "CostOptimizationStrategy",
    "SimpleLLM",
    "SlackNotifier",
    "EmailNotifier",
]
