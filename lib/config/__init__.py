from dataclasses import dataclass, field
from datetime import datetime
from functools import cached_property
from typing import Any, Dict, List, Optional

from cron_converter import Cron


@dataclass(frozen=True)
class GameProperties:
    name: str
    container_image: str
    container_path: str
    tcp_ports: List[int] = field(default_factory=list)
    udp_ports: List[int] = field(default_factory=list)
    environment: Optional[Dict[str, Any]] = None
    domain_name: Optional[str] = None
    hostname: Optional[str] = None
    auto_start: bool = False
    start_time: Optional[str] = None
    stop_time: Optional[str] = None
    enabled: bool = True
    instance_type: str = "t3a.large"
    instance_connect: bool = False

    @cached_property
    def is_operational(self) -> bool:
        if self.start_time and self.stop_time:
            now = datetime.utcnow()

            start_sched = Cron(self.start_time).schedule(start_date=now)
            stop_sched = Cron(self.stop_time).schedule(start_date=now)

            return start_sched.next() > stop_sched.next()
        return self.auto_start
