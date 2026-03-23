from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class ServiceType(Enum):
    EC2 = "EC2"
    FARGATE = "Fargate"


class PortType(Enum):
    TCP = "tcp"
    UDP = "udp"


@dataclass(frozen=True)
class GamePort:
    number: int
    port_type: PortType


@dataclass(frozen=True)
class GameProperties:

    name: str
    container_image: str
    container_path: str
    service_type: ServiceType = ServiceType.EC2
    ports: List[GamePort] = field(default_factory=list)
    environment: Optional[Dict[str, Any]] = None
    domain_name: Optional[str] = None
    hosted_zone_id: Optional[str] = None
    hostname: Optional[str] = None
    auto_start: bool = False
    start_time: Optional[str] = None
    stop_time: Optional[str] = None
    enabled: bool = True
    instance_type: str = "t3a.large"
    instance_connect: bool = False
    max_mib_memory: int = 3072
    webhook_enabled: bool = False
    idle_shutdown_minutes: int = 20
    cloudwatch_metric_namespace: Optional[str] = None
    cloudwatch_player_count_metric: Optional[str] = None

    def __post_init__(self) -> None:
        cw_fields = (self.cloudwatch_metric_namespace, self.cloudwatch_player_count_metric)
        if any(cw_fields) and not all(cw_fields):
            raise ValueError(
                "cloudwatch_metric_namespace and cloudwatch_player_count_metric "
                "must both be set or both be None"
            )
        if self.idle_shutdown_minutes <= 0 or self.idle_shutdown_minutes % 5 != 0:
            raise ValueError(
                f"idle_shutdown_minutes must be a positive multiple of 5, "
                f"got {self.idle_shutdown_minutes}"
            )
