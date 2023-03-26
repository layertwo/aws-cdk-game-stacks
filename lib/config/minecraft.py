from aws_cdk.aws_events import Schedule

from lib.config import GameProperties

EMAIL = "aws+minecraft@layertwo.dev"

ESSENTIALS_VER = "2.19.7"
VOXEL_SNIPER_VER = "8.4.3"

MODS = [
    f"https://github.com/EssentialsX/Essentials/releases/download/{ESSENTIALS_VER}/EssentialsX-{ESSENTIALS_VER}.jar",
    f"https://github.com/EssentialsX/Essentials/releases/download/{ESSENTIALS_VER}/EssentialsXChat-{ESSENTIALS_VER}.jar",
    f"https://github.com/KevinDaGame/VoxelSniper-Reimagined/releases/download/v{VOXEL_SNIPER_VER}/voxelsniper-{VOXEL_SNIPER_VER}-spigot.jar",
    "https://mediafilez.forgecdn.net/files/4162/203/worldedit-bukkit-7.2.13.jar",
    "https://mediafilez.forgecdn.net/files/4371/728/Dynmap-3.5-beta-2-spigot.jar",
]


MINECRAFT_PROPS = GameProperties(
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
        "ENABLE_QUERY": "false",
        "MAX_WORLD_SIZE": "10000",
        "MAX_PLAYERS": "10",
        "SNOOPER_ENABLED": "FALSE",
        "ENABLE_ROLLING_LOGS": "TRUE",
    },
    auto_start=True,
    start_time=Schedule.cron(minute="0", hour="23", week_day="FRI"),  # Friday 3PM PST
    stop_time=Schedule.cron(minute="0", hour="6", week_day="MON"),  # Sunday 10PM PST
    domain_name="g.layertwo.dev",
    instance_type="t3a.large",
    instance_connect=True,
)
