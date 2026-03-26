from typing import cast

import aws_cdk.aws_cloudwatch as cloudwatch
import aws_cdk.aws_ecs as ecs
from aws_cdk import Duration, Stack
from cdk_monitoring_constructs import (
    CustomMetricGroup,
    CustomMonitoringProps,
    DefaultDashboardFactory,
    MonitoringFacade,
)
from constructs import Construct

from lib.stacks.minecraft_stack import MinecraftStack


def _mc_metric(metric_name: str, server_name: str) -> cloudwatch.Metric:
    return cloudwatch.Metric(
        namespace="Minecraft",
        metric_name=metric_name,
        dimensions_map={"Server": server_name},
        statistic="Maximum",
        period=Duration.minutes(1),
    )


def _java_metric(metric_name: str, server_name: str) -> cloudwatch.Metric:
    return cloudwatch.Metric(
        namespace="Java",
        metric_name=metric_name,
        dimensions_map={"Server": server_name},
        statistic="Maximum",
        period=Duration.minutes(1),
    )


class MinecraftMonitoringStack(Stack):
    def __init__(self, scope: Construct, minecraft_stack: MinecraftStack, **kwargs) -> None:
        super().__init__(scope, "MinecraftMonitoringStack", **kwargs)
        self.add_dependency(minecraft_stack)

        s = minecraft_stack.props.name.lower()

        facade = MonitoringFacade(
            self,
            "MonitoringFacade",
            dashboard_factory=DefaultDashboardFactory(
                self,
                "DashboardFactory",
                dashboard_name_prefix="Minecraft",
            ),
        )

        # ── Section 1: ECS Infrastructure ────────────────────────────────
        facade.add_large_header("ECS Infrastructure")
        facade.monitor_simple_fargate_service(
            fargate_service=cast(ecs.FargateService, minecraft_stack.service),
        )

        # ── Section 2: Gameplay ───────────────────────────────────────────
        facade.add_large_header("Gameplay")
        facade.monitor_custom(
            CustomMonitoringProps(
                human_readable_name="Players & Server Health",
                metric_groups=[
                    CustomMetricGroup(
                        title="Players & Server Health",
                        metrics=[
                            _mc_metric("OnlinePlayers", s),
                            _mc_metric("TicksPerSecond", s),
                            _mc_metric("MaxTickTime", s),
                            _mc_metric("ChunksLoaded", s),
                        ],
                    ),
                ],
            )
        )
        facade.monitor_custom(
            CustomMonitoringProps(
                human_readable_name="World Activity",
                metric_groups=[
                    CustomMetricGroup(
                        title="World Activity",
                        metrics=[
                            _mc_metric("CreaturesSpawned", s),
                            _mc_metric("EntityDeaths", s),
                            _mc_metric("ItemsSpawned", s),
                            _mc_metric("ItemsDespawned", s),
                        ],
                    ),
                ],
            )
        )
        facade.monitor_custom(
            CustomMonitoringProps(
                human_readable_name="Player Activity",
                metric_groups=[
                    CustomMetricGroup(
                        title="Player Activity",
                        metrics=[
                            _mc_metric("PlayerInteractions", s),
                            _mc_metric("PlayerExperienceChanges", s),
                            _mc_metric("PlayerDropItems", s),
                            _mc_metric("ProjectilesLaunched", s),
                        ],
                    ),
                ],
            )
        )
        facade.monitor_custom(
            CustomMonitoringProps(
                human_readable_name="Inventory Activity",
                metric_groups=[
                    CustomMetricGroup(
                        title="Inventory Activity",
                        metrics=[
                            _mc_metric("InventoriesOpened", s),
                            _mc_metric("InventoriesClosed", s),
                            _mc_metric("InventoryClicks", s),
                            _mc_metric("InventoryDrags", s),
                        ],
                    ),
                ],
            )
        )
        facade.monitor_custom(
            CustomMonitoringProps(
                human_readable_name="World Events",
                metric_groups=[
                    CustomMetricGroup(
                        title="World Events",
                        metrics=[
                            _mc_metric("ChunksPopulated", s),
                            _mc_metric("StructuresGrown", s),
                            _mc_metric("TradesSelected", s),
                        ],
                    ),
                ],
            )
        )

        # ── Section 3: JVM Health ─────────────────────────────────────────
        facade.add_large_header("JVM Health")
        facade.monitor_custom(
            CustomMonitoringProps(
                human_readable_name="Heap Memory",
                metric_groups=[
                    CustomMetricGroup(
                        title="Heap Memory",
                        metrics=[
                            _java_metric("HeapUsedSize", s),
                            _java_metric("HeapMaxSize", s),
                            _java_metric("HeapFreeSize", s),
                            _java_metric("HeapSize", s),
                        ],
                    ),
                ],
            )
        )
        facade.monitor_custom(
            CustomMonitoringProps(
                human_readable_name="CPU & Threads",
                metric_groups=[
                    CustomMetricGroup(
                        title="CPU & Threads",
                        metrics=[
                            _java_metric("ProcessCpuLoad", s),
                            _java_metric("SystemCpuLoad", s),
                            _java_metric("Threads", s),
                            _java_metric("OpenFileDescriptors", s),
                            _java_metric("MaxFileDescriptors", s),
                        ],
                    ),
                ],
            )
        )
        facade.monitor_custom(
            CustomMonitoringProps(
                human_readable_name="Garbage Collection",
                metric_groups=[
                    CustomMetricGroup(
                        title="Garbage Collection",
                        metrics=[
                            _java_metric("GarbageCollections", s),
                            _java_metric("GarbageCollectionTime", s),
                        ],
                    ),
                ],
            )
        )
        facade.monitor_custom(
            CustomMonitoringProps(
                human_readable_name="Physical Memory",
                metric_groups=[
                    CustomMetricGroup(
                        title="Physical Memory",
                        metrics=[
                            _java_metric("TotalPhysicalMemorySize", s),
                            _java_metric("UsedPhysicalMemorySize", s),
                            _java_metric("FreePhysicalMemorySize", s),
                        ],
                    ),
                ],
            )
        )
