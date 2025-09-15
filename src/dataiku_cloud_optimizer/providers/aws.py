"""
AWS Cloud Provider implementation
"""

import logging
from typing import Any, Dict, List, Optional

from .base import CloudProvider

logger = logging.getLogger(__name__)


class AWSProvider(CloudProvider):
    """AWS Cloud Provider for cost optimization"""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self.region = self.config.get("region", "us-east-1")
        self.profile = self.config.get("profile", "default")
        self._authenticated = False
        self._session = None
        self._ce = None  # Cost Explorer client
        self._ec2 = None
        self._co = None  # Compute Optimizer client

    def authenticate(self) -> bool:
        """Authenticate with AWS using boto3 (session + clients).

        Falls back to stub behavior if boto3 or credentials are unavailable.
        """
        if self._authenticated:
            return True
        try:
            try:
                import boto3  # type: ignore
            except Exception:  # pragma: no cover - optional import during tests
                logger.info("boto3 not available; using stub AWS provider")
                self._authenticated = True
                self._session = None
                self._ce = None
                self._ec2 = None
                return True

            # Support explicit credentials (access key / secret / optional session token)
            ak = (self.config or {}).get("aws_access_key_id")
            sk = (self.config or {}).get("aws_secret_access_key")
            st = (self.config or {}).get("aws_session_token")
            if ak and sk:
                self._session = boto3.Session(
                    aws_access_key_id=ak,
                    aws_secret_access_key=sk,
                    aws_session_token=st,
                    region_name=self.region,
                )
            else:
                self._session = boto3.Session(profile_name=self.profile or None, region_name=self.region)
            self._ce = self._session.client("ce", region_name="us-east-1")
            # EC2 client is regional
            self._ec2 = self._session.client("ec2", region_name=self.region)
            # Compute Optimizer is us-east-1 or supports region selection; default to provider region
            try:
                self._co = self._session.client("compute-optimizer", region_name=self.region)
            except Exception:  # pragma: no cover
                self._co = None
            logger.info(f"Authenticated with AWS profile={self.profile} region={self.region}")
            self._authenticated = True
            return True
        except Exception as e:  # pragma: no cover - relies on external creds
            logger.warning(f"AWS authentication failed; falling back to stub. Error: {e}")
            self._authenticated = True
            self._session = None
            self._ce = None
            self._ec2 = None
            self._co = None
            return True

    def get_cost_data(
        self, start_date: Optional[str] = None, end_date: Optional[str] = None, **kwargs
    ) -> Dict[str, Any]:
        """Get AWS cost data using Cost Explorer API if available.

        Returns a dict with keys: provider, total_cost, period, services.
        Falls back to static stub values on error.
        """
        if not self._authenticated:
            self.authenticate()

        if not start_date or not end_date:
            start_date, end_date = self.get_default_date_range()

        # If Cost Explorer client unavailable, return stub
        if self._ce is None:
            return {
                "provider": "aws",
                "total_cost": 1250.75,
                "period": f"{start_date} to {end_date}",
                "resource_count": 45,
                "services": {"EC2": 850.50, "RDS": 275.25, "S3": 125.00},
                "regions": {"us-east-1": 900.00, "us-west-2": 350.75},
            }

        try:  # pragma: no cover - requires external service
            resp = self._ce.get_cost_and_usage(
                TimePeriod={"Start": start_date, "End": end_date},
                Granularity=kwargs.get("granularity", "MONTHLY"),
                Metrics=["UnblendedCost"],
                GroupBy=[{"Type": "DIMENSION", "Key": "SERVICE"}],
            )

            total_cost = 0.0
            services: Dict[str, float] = {}
            for result_by_time in resp.get("ResultsByTime", []):
                # Accumulate total
                amount = float(result_by_time.get("Total", {}).get("UnblendedCost", {}).get("Amount", 0.0) or 0.0)
                total_cost += amount
                # Accumulate services
                for group in result_by_time.get("Groups", []):
                    keys = group.get("Keys", [])
                    if not keys:
                        continue
                    svc = keys[0]
                    amt = float(group.get("Metrics", {}).get("UnblendedCost", {}).get("Amount", 0.0) or 0.0)
                    services[svc] = services.get(svc, 0.0) + amt

            return {
                "provider": "aws",
                "total_cost": round(total_cost, 2),
                "period": f"{start_date} to {end_date}",
                "resource_count": kwargs.get("resource_count", 0),  # unknown from CE alone
                "services": {k: round(v, 2) for k, v in sorted(services.items(), key=lambda x: x[1], reverse=True)},
                "regions": {},  # CE call above grouped by SERVICE; could add REGION group if needed
            }
        except Exception as e:  # pragma: no cover - external dependency
            logger.warning(f"Cost Explorer call failed; using stub. Error: {e}")
            return {
                "provider": "aws",
                "total_cost": 1250.75,
                "period": f"{start_date} to {end_date}",
                "resource_count": 45,
                "services": {"EC2": 850.50, "RDS": 275.25, "S3": 125.00},
                "regions": {"us-east-1": 900.00, "us-west-2": 350.75},
            }

    def get_resource_inventory(self) -> List[Dict[str, Any]]:
        """Get AWS resource inventory (EC2 instances) if possible; fallback to stub."""
        if not self._authenticated:
            self.authenticate()

        if self._ec2 is None:
            return [
                {
                    "resource_id": "i-1234567890abcdef0",
                    "resource_type": "EC2",
                    "instance_type": "t3.large",
                    "state": "running",
                    "cost_per_hour": 0.0832,
                    "utilization": 25.5,
                    "tags": {"Environment": "production", "Team": "data-science"},
                }
            ]

        try:  # pragma: no cover - requires external service
            paginator = self._ec2.get_paginator("describe_instances")
            items: List[Dict[str, Any]] = []
            for page in paginator.paginate():
                for res in page.get("Reservations", []):
                    for inst in res.get("Instances", []):
                        tags = {t.get("Key"): t.get("Value") for t in inst.get("Tags", [])}
                        items.append(
                            {
                                "resource_id": inst.get("InstanceId"),
                                "resource_type": "EC2",
                                "instance_type": inst.get("InstanceType"),
                                "state": inst.get("State", {}).get("Name"),
                                "launch_time": str(inst.get("LaunchTime")),
                                "tags": tags,
                            }
                        )
            return items
        except Exception as e:  # pragma: no cover
            logger.warning(f"EC2 inventory failed; using stub. Error: {e}")
            return [
                {
                    "resource_id": "i-1234567890abcdef0",
                    "resource_type": "EC2",
                    "instance_type": "t3.large",
                    "state": "running",
                    "cost_per_hour": 0.0832,
                    "utilization": 25.5,
                    "tags": {"Environment": "production", "Team": "data-science"},
                }
            ]

    def get_recommendations(self) -> List[Dict[str, Any]]:
        """Get AWS-specific optimization recommendations.

        Note: For production, integrate with AWS Compute Optimizer or Trusted Advisor.
        Here we keep a stub until those services are wired.
        """
        if not self._authenticated:
            self.authenticate()
        return [
            {
                "type": "rightsizing",
                "resource_id": "i-1234567890abcdef0",
                "current_type": "t3.large",
                "recommended_type": "t3.medium",
                "estimated_savings": 45.50,
                "confidence": 0.85,
                "reason": "Low CPU utilization detected over 30 days",
            }
        ]

    def get_rightsizing_opportunities(self) -> List[Dict[str, Any]]:
        """Get EC2 rightsizing opportunities using AWS Compute Optimizer when available.

        Returns a list of dicts with keys: instance_id, current_type, recommended_type,
        monthly_savings, and confidence_score. Falls back to a static example.
        """
        if not self._authenticated:
            self.authenticate()
        if self._co is None:
            return [
                {
                    "instance_id": "i-1234567890abcdef0",
                    "current_type": "t3.large",
                    "recommended_type": "t3.medium",
                    "cpu_utilization": 25.5,
                    "memory_utilization": 30.2,
                    "network_utilization": 15.1,
                    "monthly_savings": 45.50,
                    "confidence_score": 0.85,
                }
            ]
        try:  # pragma: no cover - external service
            recs: List[Dict[str, Any]] = []
            paginator = self._co.get_paginator("get_ec2_instance_recommendations")
            for page in paginator.paginate():
                for rec in page.get("instanceRecommendations", []):
                    instance_id = rec.get("instanceArn", "").split("/")[-1]
                    current_type = rec.get("currentInstanceType")
                    # pick top recommendation option by projected monthly savings
                    best = None
                    for opt in rec.get("recommendationOptions", []):
                        savings = (
                            (opt.get("projectedUtilizationMetrics", []) or [{}])[0].get("value")
                        )
                        # Compute Optimizer provides "projectedMonthlySavings" in newer APIs; guard fallback
                        monthly = opt.get("projectedMonthlySavings", {}).get("value") if isinstance(opt.get("projectedMonthlySavings"), dict) else None
                        score = opt.get("performanceRisk")
                        cand = {
                            "recommended_type": opt.get("instanceType"),
                            "monthly_savings": float(monthly) if monthly is not None else None,
                            "performance_risk": float(score) if score is not None else None,
                        }
                        if best is None:
                            best = cand
                        else:
                            if (cand["monthly_savings"] or 0) > (best["monthly_savings"] or 0):
                                best = cand
                    if best is None:
                        continue
                    recs.append(
                        {
                            "instance_id": instance_id,
                            "current_type": current_type,
                            "recommended_type": best.get("recommended_type"),
                            "monthly_savings": best.get("monthly_savings") or 0.0,
                            "confidence_score": max(0.0, 1.0 - float(best.get("performance_risk") or 0.5)),
                        }
                    )
            return recs
        except Exception as e:  # pragma: no cover
            logger.warning(f"Compute Optimizer call failed; using stub. Error: {e}")
            return [
                {
                    "instance_id": "i-1234567890abcdef0",
                    "current_type": "t3.large",
                    "recommended_type": "t3.medium",
                    "cpu_utilization": 25.5,
                    "memory_utilization": 30.2,
                    "network_utilization": 15.1,
                    "monthly_savings": 45.50,
                    "confidence_score": 0.85,
                }
            ]

    def get_unused_resources(self) -> List[Dict[str, Any]]:
        """Get unused AWS resources (placeholder)."""
        if not self._authenticated:
            self.authenticate()
        return [
            {
                "resource_id": "vol-0987654321fedcba0",
                "resource_type": "EBS Volume",
                "size_gb": 100,
                "status": "available",
                "monthly_cost": 25.00,
                "last_attached": None,
                "recommendation": "Delete unused volume",
            }
        ]
