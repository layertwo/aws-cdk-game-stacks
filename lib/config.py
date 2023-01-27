from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


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
    enabled: bool = True


ESSENTIALS_VER = "2.19.7"
ESSENTIALS_URL = f"https://github.com/EssentialsX/Essentials/releases/download/{ESSENTIALS_VER}"
ESSENTIALS_PLUGINS = ["EssentialsX", "EssentialsXChat"]
MODS = ",".join(f"{ESSENTIALS_URL}/{p}-{ESSENTIALS_VER}.jar" for p in ESSENTIALS_PLUGINS)

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
            "MODS": MODS,
        },
        auto_start=True,
        hosted_zone="Z09871391DBKPQ6VVS5KY",
    )
]
