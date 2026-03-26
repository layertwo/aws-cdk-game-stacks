from typing import Mapping

import aws_cdk.aws_cloudwatch as cw
from aws_cdk import Duration
from aws_cdk import aws_ecs as ecs
from aws_cdk import aws_iam as iam
from aws_cdk import aws_logs as logs
from aws_cdk import aws_sns as sns
from aws_cdk import aws_sns_subscriptions as sns_subscriptions
from cdk_monitoring_constructs import (
    AlarmFactoryDefaults,
    CustomMetricGroup,
    CustomMetricWithAlarm,
    CustomThreshold,
    DefaultDashboardFactory,
    MonitoringFacade,
    SnsAlarmActionStrategy,
)
from constructs import Construct

from lib.config import GameProperties, ServiceType
from lib.stacks.game_stack import GameStack, PortType


class MinecraftStack(GameStack):
    def __init__(self, scope: Construct, props: GameProperties, **kwargs) -> None:
        """Minecraft Stack"""
        super().__init__(scope, props, **kwargs)
        self.add_metric_to_task_role()
        self.topic = self.create_alarm_topic()
        self.create_monitoring()

    def _create_container(self) -> ecs.ContainerDefinition:
        """
        Custom container create for Minecraft
        """
        container = self.task.add_container(
            f"{self.props.name}Container",
            image=ecs.ContainerImage.from_registry(self.props.container_image),
            essential=True,
            logging=ecs.LogDrivers.aws_logs(
                stream_prefix=self.props.name,
                log_retention=logs.RetentionDays.ONE_WEEK,
            ),
            cpu=2048,
            memory_limit_mib=self.props.max_mib_memory,
            environment=self.props.environment,
        )
        for port in self.props.ports:
            if port.port_type == PortType.TCP:
                proto = ecs.Protocol.TCP
            elif port.port_type == PortType.UDP:  # pragma: nocover
                proto = ecs.Protocol.UDP
            container.add_port_mappings(
                ecs.PortMapping(container_port=port.number, host_port=port.number, protocol=proto)
            )

        container.add_mount_points(
            ecs.MountPoint(
                container_path=self.props.container_path,
                source_volume=self.ecs_volume.name,
                read_only=False,
            )
        )
        return container

    def add_metric_to_task_role(self) -> None:
        # allow task to publish cloudwatch metrics
        self.task.add_to_task_role_policy(
            iam.PolicyStatement(actions=["cloudwatch:PutMetricData"], resources=["*"])
        )

    @property
    def _dimensions_map(self) -> Mapping[str, str]:
        return {"Server": self.props.name.lower()}

    def _mc_metric(self, metric_name: str) -> cw.Metric:
        return cw.Metric(
            namespace="Minecraft",
            metric_name=metric_name,
            dimensions_map=self._dimensions_map,
            statistic="Maximum",
            period=Duration.minutes(1),
        )

    def _java_metric(self, metric_name: str) -> cw.Metric:
        return cw.Metric(
            namespace="Java",
            metric_name=metric_name,
            dimensions_map=self._dimensions_map,
            statistic="Maximum",
            period=Duration.minutes(1),
        )

    def create_alarm_topic(self) -> sns.Topic:
        topic = sns.Topic(self, self.qualify_name("WatchdogTopic"))
        topic.add_subscription(sns_subscriptions.LambdaSubscription(self.task_count_lambda))
        return topic

    def create_monitoring(self) -> MonitoringFacade:

        facade = MonitoringFacade(
            self,
            f"{self.props.name}-Monitoring-Dashboard",
            alarm_factory_defaults=AlarmFactoryDefaults(
                alarm_name_prefix=self.props.name,
                actions_enabled=True,
            ),
        )

        if self.props.service_type == ServiceType.FARGATE:
            facade.add_large_header("ECS (Fargate) Infrastructure")
            facade.monitor_simple_fargate_service(
                fargate_service=self.service,
            )
        elif self.props.service_type == ServiceType.EC2:  # pragma: nocover
            facade.add_large_header("ECS (EC2) Infrastructure")
            facade.monitor_simple_ec2_service(
                ec2_service=self.service,
            )

        facade.add_large_header("Gameplay")
        facade.monitor_custom(
            alarm_friendly_name="Players & Server Health",
            metric_groups=[
                CustomMetricGroup(
                    title="Player Count",
                    metrics=[
                        CustomMetricWithAlarm(
                            metric=self._mc_metric("OnlinePlayers"),
                            alarm_friendly_name="Online-Player-Count-0",
                            add_alarm={
                                "Warning": CustomThreshold(
                                    threshold=0,
                                    comparison_operator=cw.ComparisonOperator.LESS_THAN_OR_EQUAL_TO_THRESHOLD,
                                    evaluation_periods=self.props.idle_shutdown_minutes,
                                    datapoints_to_alarm=self.props.idle_shutdown_minutes,
                                    treat_missing_data_override=cw.TreatMissingData.BREACHING,
                                    action_override=SnsAlarmActionStrategy(
                                        on_alarm_topic=self.topic
                                    ),
                                )
                            },
                        )
                    ],
                ),
                CustomMetricGroup(
                    title="Server Health",
                    metrics=[
                        self._mc_metric("TicksPerSecond"),
                        self._mc_metric("MaxTickTime"),
                        self._mc_metric("ChunksLoaded"),
                    ],
                ),
            ],
        )
        facade.monitor_custom(
            alarm_friendly_name="World Activity",
            metric_groups=[
                CustomMetricGroup(
                    title="World Activity",
                    metrics=[
                        self._mc_metric("CreaturesSpawned"),
                        self._mc_metric("EntityDeaths"),
                        self._mc_metric("ItemsSpawned"),
                        self._mc_metric("ItemsDespawned"),
                    ],
                ),
            ],
        )
        facade.monitor_custom(
            alarm_friendly_name="Player Activity",
            metric_groups=[
                CustomMetricGroup(
                    title="Player Activity",
                    metrics=[
                        self._mc_metric("PlayerInteractions"),
                        self._mc_metric("PlayerExperienceChanges"),
                        self._mc_metric("PlayerDropItems"),
                        self._mc_metric("ProjectilesLaunched"),
                    ],
                ),
            ],
        )
        facade.monitor_custom(
            alarm_friendly_name="Inventory Activity",
            metric_groups=[
                CustomMetricGroup(
                    title="Inventory Activity",
                    metrics=[
                        self._mc_metric("InventoriesOpened"),
                        self._mc_metric("InventoriesClosed"),
                        self._mc_metric("InventoryClicks"),
                        self._mc_metric("InventoryDrags"),
                    ],
                ),
            ],
        )
        facade.monitor_custom(
            alarm_friendly_name="World Events",
            metric_groups=[
                CustomMetricGroup(
                    title="World Events",
                    metrics=[
                        self._mc_metric("ChunksPopulated"),
                        self._mc_metric("StructuresGrown"),
                        self._mc_metric("TradesSelected"),
                    ],
                ),
            ],
        )

        facade.add_large_header("JVM Health")
        facade.monitor_custom(
            alarm_friendly_name="Heap Memory",
            metric_groups=[
                CustomMetricGroup(
                    title="Heap Memory",
                    metrics=[
                        self._java_metric("HeapUsedSize"),
                        self._java_metric("HeapMaxSize"),
                        self._java_metric("HeapFreeSize"),
                        self._java_metric("HeapSize"),
                    ],
                ),
            ],
        )
        facade.monitor_custom(
            alarm_friendly_name="CPU & Threads",
            metric_groups=[
                CustomMetricGroup(
                    title="CPU",
                    metrics=[
                        self._java_metric("ProcessCpuLoad"),
                        self._java_metric("SystemCpuLoad"),
                    ],
                ),
                CustomMetricGroup(
                    title="Threads / IO",
                    metrics=[
                        self._java_metric("Threads"),
                        self._java_metric("OpenFileDescriptors"),
                        self._java_metric("MaxFileDescriptors"),
                    ],
                ),
            ],
        )
        facade.monitor_custom(
            alarm_friendly_name="Garbage Collection",
            metric_groups=[
                CustomMetricGroup(
                    title="Garbage Collection",
                    metrics=[
                        self._java_metric("GarbageCollections"),
                        self._java_metric("GarbageCollectionTime"),
                    ],
                ),
            ],
        )
        facade.monitor_custom(
            alarm_friendly_name="Physical Memory",
            metric_groups=[
                CustomMetricGroup(
                    title="Physical Memory",
                    metrics=[
                        self._java_metric("TotalPhysicalMemorySize"),
                        self._java_metric("UsedPhysicalMemorySize"),
                        self._java_metric("FreePhysicalMemorySize"),
                    ],
                ),
            ],
        )
