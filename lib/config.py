from dataclasses import dataclass, field
from datetime import datetime
from functools import cached_property
from typing import Any, Dict, List, Optional

from aws_cdk.aws_events import Schedule

from lib.aws_common.events import convert_schedule_to_cron


@dataclass(frozen=True)
class GameProperties:
    name: str
    container_image: str
    container_path: str
    tcp_ports: List[int] = field(default_factory=list)
    udp_ports: List[int] = field(default_factory=list)
    environment: Optional[Dict[str, Any]] = None
    hosted_zone: Optional[str] = None
    hostname: Optional[str] = None
    auto_start: bool = False
    start_time: Optional[Schedule] = None
    stop_time: Optional[Schedule] = None
    enabled: bool = True
    instance_connect: bool = False

    @cached_property
    def is_operational(self) -> bool:
        if self.start_time and self.stop_time:
            start_cron = convert_schedule_to_cron(self.start_time)
            stop_cron = convert_schedule_to_cron(self.stop_time)
            now = datetime.utcnow()

            start_sched = start_cron.schedule(start_date=now)
            stop_sched = stop_cron.schedule(start_date=now)

            return start_sched.next() > stop_sched.next()
        return self.auto_start


ESSENTIALS_VER = "2.19.7"
VOXEL_SNIPER_VER = "8.4.3"

MODS = [
    f"https://github.com/EssentialsX/Essentials/releases/download/{ESSENTIALS_VER}/EssentialsX-{ESSENTIALS_VER}.jar",
    f"https://github.com/EssentialsX/Essentials/releases/download/{ESSENTIALS_VER}/EssentialsXChat-{ESSENTIALS_VER}.jar",
    f"https://github.com/KevinDaGame/VoxelSniper-Reimagined/releases/download/v{VOXEL_SNIPER_VER}/voxelsniper-{VOXEL_SNIPER_VER}-spigot.jar",
    "https://mediafilez.forgecdn.net/files/4162/203/worldedit-bukkit-7.2.13.jar",
]


ALL_GAME_PROPS = [
    GameProperties(
        name="Minecraft",
        container_image="itzg/minecraft-server:java17-jdk",
        container_path="/data",
        tcp_ports=[25565],
        environment={
            "TYPE": "PAPER",
            "EULA": "TRUE",
            "VERSION": "1.19.3",
            "MAX_MEMORY": "6144M",
            "MAX_TICK_TIME": "60000",
            "SPIGET_RESOURCES": "390",
            "MODS": ",".join(MODS),
        },
        auto_start=True,
        start_time=Schedule.cron(minute="0", hour="23", week_day="FRI"),  # Friday 3PM PST
        stop_time=Schedule.cron(minute="0", hour="6", week_day="MON"),  # Sunday 10PM PST
        hosted_zone="Z09871391DBKPQ6VVS5KY",
        instance_connect=True,
    )
]
