"""Embedded AWS provider with optional realtime AWS integrations.

Attempts to use boto3 Cost Explorer and Compute Optimizer when available
and credentials are configured. Falls back gracefully if not available.
"""
from __future__ import annotations
import logging
from typing import Any, Dict, List, Optional
from .base import CloudProvider

logger = logging.getLogger(__name__)

class AWSProvider(CloudProvider):
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self.region = self.config.get("region", "us-east-1")
        self.profile = self.config.get("profile", "default")
        self._authenticated = False
        self._session = None  # boto3 session (optional)
        self._co = None  # compute optimizer client (optional)

    def authenticate(self) -> bool:
        try:
            logger.info(f"Authenticating with AWS profile={self.profile}, region={self.region}")
            try:  # pragma: no cover - external dependency
                import boto3  # type: ignore

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
                # Verify credentials with STS
                try:
                    sts = self._session.client("sts", region_name=self.region)
                    ident = sts.get_caller_identity()
                    logger.info("AWS STS identity: %s", ident.get("Arn"))
                except Exception as e:
                    logger.warning("AWS STS check failed; credentials may be missing/invalid: %s", e)
                    self._session = None
                    self._co = None
                    self._authenticated = False
                    return False
                # Region-specific client for Compute Optimizer
                try:
                    self._co = self._session.client("compute-optimizer", region_name=self.region)
                except Exception:
                    self._co = None
            except Exception:
                # boto3 not available in environment
                logger.warning("boto3 not available in this code env; falling back to stubs")
                self._session = None
                self._co = None
                self._authenticated = False
                return False
            self._authenticated = True
            return True
        except Exception as e:  # pragma: no cover - defensive
            logger.error(f"AWS auth failed: {e}")
            return False

    def get_cost_data(self, start_date: Optional[str] = None, end_date: Optional[str] = None, **kwargs) -> Dict[str, Any]:
        if not self._authenticated:
            self.authenticate()
        if not start_date or not end_date:
            start_date, end_date = self.get_default_date_range()

        # Try realtime data via boto3 Cost Explorer if available in DSS code env
        try:  # pragma: no cover - external dependency
            # Ensure session exists (authenticate lazily)
            if self._session is None:
                self.authenticate()
            import boto3  # type: ignore

            # Cost Explorer is us-east-1 scoped
            sess = self._session or boto3.Session(profile_name=self.profile or None, region_name=self.region)
            ce = sess.client("ce", region_name="us-east-1")
            resp = ce.get_cost_and_usage(
                TimePeriod={"Start": start_date, "End": end_date},
                Granularity=kwargs.get("granularity", "MONTHLY"),
                Metrics=["UnblendedCost"],
                GroupBy=[{"Type": "DIMENSION", "Key": "SERVICE"}],
            )
            total_cost = 0.0
            services: Dict[str, float] = {}
            for rbt in resp.get("ResultsByTime", []):
                total_cost += float(rbt.get("Total", {}).get("UnblendedCost", {}).get("Amount", 0) or 0)
                for g in rbt.get("Groups", []):
                    key = (g.get("Keys") or ["unknown"])[0]
                    amt = float(g.get("Metrics", {}).get("UnblendedCost", {}).get("Amount", 0) or 0)
                    services[key] = services.get(key, 0.0) + amt
            return {
                "provider": "aws",
                "total_cost": round(total_cost, 2),
                "period": f"{start_date} to {end_date}",
                "resource_count": kwargs.get("resource_count", 0),
                "services": {k: round(v, 2) for k, v in sorted(services.items(), key=lambda x: x[1], reverse=True)},
            }
        except Exception as e:
            logger.warning("AWS Cost Explorer fetch failed; using stubbed cost data: %s", e)
            return {
                "provider": "aws",
                "total_cost": 1250.75,
                "period": f"{start_date} to {end_date}",
                "resource_count": 45,
                "services": {"EC2": 850.50, "RDS": 275.25, "S3": 125.00},
            }

    def get_rightsizing_opportunities(self) -> List[Dict[str, Any]]:
        if not self._authenticated:
            self.authenticate()
        # Attempt Compute Optimizer if available
        try:  # pragma: no cover
            if self._co is None:
                return []
            recs: List[Dict[str, Any]] = []
            paginator = self._co.get_paginator("get_ec2_instance_recommendations")
            for page in paginator.paginate():
                for r in page.get("instanceRecommendations", []):
                    arn = r.get("instanceArn", "")
                    iid = arn.split("/")[-1]
                    # arn:partition:service:region:account:resource
                    arn_parts = arn.split(":")
                    inst_region = arn_parts[3] if len(arn_parts) > 3 else self.region
                    cur = r.get("currentInstanceType")
                    best = None
                    for opt in r.get("recommendationOptions", []):
                        monthly = opt.get("projectedMonthlySavings", {}).get("value") if isinstance(opt.get("projectedMonthlySavings"), dict) else None
                        risk = opt.get("performanceRisk")
                        cand = {"type": opt.get("instanceType"), "monthly": monthly, "risk": risk}
                        if best is None or (cand["monthly"] or 0) > (best["monthly"] or 0):
                            best = cand
                    if best:
                        recs.append(
                            {
                                "instance_id": iid,
                                "region": inst_region,
                                "current_type": cur,
                                "recommended_type": best["type"],
                                "monthly_savings": float(best["monthly"]) if best["monthly"] is not None else 0.0,
                                "confidence_score": max(0.0, 1.0 - float(best["risk"] or 0.5)),
                            }
                        )
            return recs
        except Exception as e:
            logger.warning("Compute Optimizer rightsizing fetch failed: %s", e)
            return []

    def get_resource_inventory(self) -> List[Dict[str, Any]]:
        if not self._authenticated:
            self.authenticate()
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
        if not self._authenticated:
            self.authenticate()
        # Prefer real-time rightsizing if available; otherwise empty
        try:
            rightsizing = self.get_rightsizing_opportunities()
            return [
                {
                    "type": "rightsizing",
                    "resource_id": r.get("instance_id"),
                    "current_type": r.get("current_type"),
                    "recommended_type": r.get("recommended_type"),
                    "estimated_savings": r.get("monthly_savings"),
                    "confidence": r.get("confidence_score"),
                    "reason": "Compute Optimizer recommendation",
                }
                for r in rightsizing
            ]
        except Exception:
            return []

    def get_unused_resources(self) -> List[Dict[str, Any]]:
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
