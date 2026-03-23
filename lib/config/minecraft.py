from lib.config import GamePort, GameProperties, PortType, ServiceType

EMAIL = "aws+minecraft@layertwo.dev"

MC_VERSION = "1.21.1"
ESSENTIALS_VER = "2.21.2"
VOXEL_SNIPER_VER = "8.14.0"
MV_CORE = "5.5.3"
MV_INV = "5.3.2"

MODS = [
    # Essentials
    f"https://github.com/EssentialsX/Essentials/releases/download/{ESSENTIALS_VER}/EssentialsX-{ESSENTIALS_VER}.jar",
    f"https://github.com/EssentialsX/Essentials/releases/download/{ESSENTIALS_VER}/EssentialsXChat-{ESSENTIALS_VER}.jar",
    f"https://github.com/EssentialsX/Essentials/releases/download/{ESSENTIALS_VER}/EssentialsXSpawn-{ESSENTIALS_VER}.jar",
    # World Management
    f"https://github.com/KevinDaGame/VoxelSniper-Reimagined/releases/download/v{VOXEL_SNIPER_VER}/voxelsniper-{VOXEL_SNIPER_VER}-spigot.jar",
    "https://mediafilez.forgecdn.net/files/4954/406/worldedit-bukkit-7.2.18-dist.jar",
    "https://mediafilez.forgecdn.net/files/4675/318/worldguard-bukkit-7.0.9-dist.jar",
    "https://github.com/layertwo/WeatherMan/releases/download/2.0.0/WeatherMan-2.0.0.jar",
    "https://github.com/layertwo/SpigotPing/releases/download/2.7.0/SpigotPing-2.7.0.jar",
    # Multiverse
    f"https://github.com/Multiverse/Multiverse-Core/releases/download/{MV_CORE}/multiverse-core-{MV_CORE}.jar",
    f"https://github.com/Multiverse/Multiverse-Inventories/releases/download/{MV_INV}/multiverse-inventories-{MV_INV}.jar",
    # Permissions
    "https://download.luckperms.net/1626/bukkit/loader/LuckPerms-Bukkit-5.5.38.jar"
    "https://mediafilez.forgecdn.net/files/3007/470/Vault.jar",
    # Transportation
    "https://ci.mg-dev.eu/job/TrainCarts/1686/artifact/build/TrainCarts-1.21.11-v2-1686.jar",
    "https://ci.mg-dev.eu/job/BKCommonLib/1957/artifact/build/BKCommonLib-1.21.11-v1-1957.jar",
    # World viewing
    # "https://cdn.modrinth.com/data/YMXhf1UJ/versions/Aziw81Ii/Pl3xMap-1.20.1-469.jar",
    "https://github.com/DecentSoftware-eu/DecentHolograms/releases/download/2.9.9/DecentHolograms-2.9.9.jar",
    # Monitoring - AWS
    "https://github.com/layertwo/Spigot-Cloudwatch/releases/download/v1.2.0/CloudWatch-1.2.0.jar",
]

MAX_MEMORY = 6144
MINECRAFT_PROPS = GameProperties(
    name="Minecraft",
    container_image="itzg/minecraft-server:java17-jdk",
    container_path="/data",
    service_type=ServiceType.FARGATE,
    ports=[GamePort(port_type=PortType.TCP, number=25565)],
    environment={
        "TYPE": "PAPER",
        "EULA": "TRUE",
        "VERSION": MC_VERSION,
        "MAX_MEMORY": f"{MAX_MEMORY}M",
        "MAX_TICK_TIME": "60000",
        "MODS": ",".join(MODS),
        "REMOVE_OLD_MODS": "TRUE",
        "REMOVE_OLD_MODS_INCLUDE": "*.jar",
        "REMOVE_OLD_MODS_EXCLUDE": "",
        "REMOVE_OLD_MODS_DEPTH": "1",
        "ENABLE_QUERY": "false",
        "MAX_WORLD_SIZE": "10000",
        "MAX_PLAYERS": "10",
        "SNOOPER_ENABLED": "FALSE",
        "ENABLE_ROLLING_LOGS": "TRUE",
        "USE_AIKAR_FLAGS": "TRUE",
        "USE_FLARE_FLAGS": "FALSE",
    },
    auto_start=False,
    start_time="0 23 * * FRI",  # Friday 3PM PST
    stop_time="0 6 * * MON",  # Sunday 10PM PST,
    domain_name="g.layertwo.dev",
    hosted_zone_id="Z09871391DBKPQ6VVS5KY",
    instance_type="t4g.large",
    instance_connect=False,
    max_mib_memory=MAX_MEMORY,
)
