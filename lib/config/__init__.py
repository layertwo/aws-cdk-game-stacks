from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


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
