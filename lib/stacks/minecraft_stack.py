from aws_cdk import aws_ecs as ecs
from aws_cdk import aws_iam as iam
from aws_cdk import aws_logs as logs
from constructs import Construct

from lib.config import GameProperties
from lib.stacks.game_stack import GameStack, PortType


class MinecraftStack(GameStack):
    def __init__(self, scope: Construct, props: GameProperties, **kwargs) -> None:
        """Minecraft Stack"""
        super().__init__(scope, props, **kwargs)
        self.add_metric_to_task_role()

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
            elif port.port_type == PortType.UDP:
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
