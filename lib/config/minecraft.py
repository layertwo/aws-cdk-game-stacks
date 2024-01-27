from lib.config import GamePort, GameProperties, PortType

EMAIL = "aws+minecraft@layertwo.dev"

ESSENTIALS_VER = "2.20.1"
VOXEL_SNIPER_VER = "8.12.4"
MV_CORE = "4.3.12"
MV_INV = "4.2.6"

MODS = [
    # Essentials
    f"https://github.com/EssentialsX/Essentials/releases/download/{ESSENTIALS_VER}/EssentialsX-{ESSENTIALS_VER}.jar",
    f"https://github.com/EssentialsX/Essentials/releases/download/{ESSENTIALS_VER}/EssentialsXChat-{ESSENTIALS_VER}.jar",
    f"https://github.com/EssentialsX/Essentials/releases/download/{ESSENTIALS_VER}/EssentialsXSpawn-{ESSENTIALS_VER}.jar",
    # World Management
    f"https://github.com/KevinDaGame/VoxelSniper-Reimagined/releases/download/v{VOXEL_SNIPER_VER}/voxelsniper-{VOXEL_SNIPER_VER}-spigot.jar",
    "https://mediafilez.forgecdn.net/files/4586/220/worldedit-bukkit-7.2.15.jar",
    "https://mediafilez.forgecdn.net/files/4675/318/worldguard-bukkit-7.0.9-dist.jar",
    "https://github.com/layertwo/WeatherMan/releases/download/2.0.0/WeatherMan-2.0.0.jar",
    "https://github.com/layertwo/SpigotPing/releases/download/2.7.0/SpigotPing-2.7.0.jar",
    # Multiverse
    f"https://github.com/Multiverse/Multiverse-Core/releases/download/{MV_CORE}/multiverse-core-{MV_CORE}.jar",
    f"https://github.com/Multiverse/Multiverse-Inventories/releases/download/{MV_INV}/multiverse-inventories-{MV_INV}.jar",
    # Permissions
    "https://download.luckperms.net/1515/bukkit/loader/LuckPerms-Bukkit-5.4.102.jar",
    "https://mediafilez.forgecdn.net/files/3007/470/Vault.jar",
    # Transportation
    "https://ci.mg-dev.eu/job/TrainCarts/1418/artifact/target/TrainCarts-1.20.1-v2-1418.jar",
    "https://ci.mg-dev.eu/job/BKCommonLib/1613/artifact/build/BKCommonLib-1.20.1-v3-1613.jar",
    # World viewing
    # "https://cdn.modrinth.com/data/YMXhf1UJ/versions/Aziw81Ii/Pl3xMap-1.20.1-469.jar",
    "https://github.com/DecentSoftware-eu/DecentHolograms/releases/download/2.8.3/DecentHolograms-2.8.3.jar",
    # Monitoring - AWS
    "https://github.com/layertwo/Spigot-Cloudwatch/releases/download/v1.2.0/CloudWatch-1.2.0.jar",
]

MAX_MEMORY = 3072
MINECRAFT_PROPS = GameProperties(
    name="Minecraft",
    container_image="itzg/minecraft-server:java17-jdk",
    container_path="/data",
    ports=[GamePort(port_type=PortType.TCP, number=25565)],
    environment={
        "TYPE": "PAPER",
        "EULA": "TRUE",
        "VERSION": "1.20.1",
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
    auto_start=True,
    start_time="0 23 * * FRI",  # Friday 3PM PST
    stop_time="0 6 * * MON",  # Sunday 10PM PST,
    domain_name="g.layertwo.dev",
    hosted_zone_id="Z09871391DBKPQ6VVS5KY",
    instance_type="t4g.medium",
    instance_connect=True,
    max_mib_memory=MAX_MEMORY,
)
