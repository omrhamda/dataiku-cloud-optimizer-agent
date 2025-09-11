"""Provider implementations (embedded stubs for DSS plugin)."""
from .aws import AWSProvider
from .azure import AzureProvider
from .gcp import GCPProvider

__all__ = ["AWSProvider", "AzureProvider", "GCPProvider"]
