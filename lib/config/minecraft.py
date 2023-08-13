from lib.config import GameProperties

EMAIL = "aws+minecraft@layertwo.dev"

ESSENTIALS_VER = "2.20.1"
VOXEL_SNIPER_VER = "8.12.2"

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
    "https://github.com/Multiverse/Multiverse-Core/releases/download/4.3.9/multiverse-core-4.3.9.jar",
    "https://github.com/Multiverse/Multiverse-Inventories/releases/download/4.2.5/multiverse-inventories-4.2.5.jar",
    # Permissions
    "https://download.luckperms.net/1512/bukkit/loader/LuckPerms-Bukkit-5.4.98.jar",
    "https://mediafilez.forgecdn.net/files/3007/470/Vault.jar",
    # Transportation
    "https://ci.mg-dev.eu/job/TrainCarts/1412/artifact/target/TrainCarts-1.20.1-v1-1412.jar",
    "https://ci.mg-dev.eu/job/BKCommonLib/1586/artifact/build/BKCommonLib-1.20.1-v1-1586.jar",
    # World viewing
    "https://mediafilez.forgecdn.net/files/4632/182/Dynmap-3.6-spigot.jar",
    # Monitoring - AWS
    "https://github.com/layertwo/Spigot-Cloudwatch/releases/download/v1.2.0/CloudWatch-1.2.0.jar",
]

MINECRAFT_PROPS = GameProperties(
    name="Minecraft",
    container_image="itzg/minecraft-server:java17-jdk",
    container_path="/data",
    tcp_ports=[25565],
    environment={
        "TYPE": "PURPUR",
        "EULA": "TRUE",
        "VERSION": "1.20.1",
        "MAX_MEMORY": "6144M",
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
    },
    auto_start=True,
    start_time="0 23 * * FRI",  # Friday 3PM PST
    stop_time="0 6 * * MON",  # Sunday 10PM PST,
    domain_name="g.layertwo.dev",
    instance_type="t4g.large",
    instance_connect=True,
)
