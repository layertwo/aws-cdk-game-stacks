from aws_cdk import aws_ecs as ecs
from aws_cdk import aws_iam as iam
from constructs import Construct

from lib.aws_common.ecs import build_container
from lib.config import GameProperties
from lib.constructs.traefik import TraefikService
from lib.stacks.game_stack import GameStack, PortType


class MinecraftStack(GameStack):
    def __init__(self, scope: Construct, props: GameProperties, **kwargs) -> None:
        """Minecraft Stack"""
        super().__init__(scope, props, **kwargs)
        self.create_traefik_service()
        self.add_metric_to_task_role()

    def _create_container(self) -> ecs.ContainerDefinition:
        """
        Custom container create for Minecraft
        """
        container = build_container(
            task=self.task,
            name=self.props.name,
            container_image=self.props.container_image,
            cpu=1920,
            memory_limit_mib=6144,
            environment=self.props.environment,
            docker_labels={
                "traefik.enable": "true",
                "traefik.http.routers.dynmap-https.rule": f"Host(`{self.fqdn}`)",
                "traefik.http.services.dynmap-https.loadbalancer.server.port": "8080",
                "traefik.http.routers.dynmap-https.entrypoints": "websecure",
                "traefik.http.routers.dynmap-https.service": "dynmap-https",
                "traefik.http.routers.dynmap-https.tls": "true",
                "traefik.http.routers.dynmap-https.tls.certresolver": "le",
            },
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

    def add_metric_to_task_role(self) -> None:
        # allow task to publish cloudwatch metrics
        self.task.add_to_task_role_policy(
            iam.PolicyStatement(actions=["cloudwatch:PutMetricData"], resources=["*"])
        )

    def create_traefik_service(self) -> TraefikService:
        return TraefikService(
            self,
            "TraefikService",
            cluster=self.cluster,
            security_group=self.instance_security_group,
        )
