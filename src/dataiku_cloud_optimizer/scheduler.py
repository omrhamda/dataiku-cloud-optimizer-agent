"""
Background scheduler to run proactive optimization cycles periodically.
"""

from typing import List, Optional

from apscheduler.schedulers.background import BackgroundScheduler  # type: ignore

from .core import CloudOptimizerAgent


class AgentScheduler:
    def __init__(self, agent: CloudOptimizerAgent) -> None:
        self.agent = agent
        self._sched = BackgroundScheduler()
        self._job = None

    def start(
        self,
        interval_minutes: int = 1440,
        provider: Optional[str] = None,
        channels: Optional[List[str]] = None,
    ) -> None:
        if self._job:
            self._job.remove()
        self._job = self._sched.add_job(
            lambda: self.agent.run_proactive_cycle(
                provider=provider, channels=channels
            ),
            "interval",
            minutes=interval_minutes,
            replace_existing=True,
            id="proactive-cycle",
        )
        if not self._sched.running:
            self._sched.start()

    def stop(self) -> None:
        if self._sched.running:
            self._sched.shutdown(wait=False)
