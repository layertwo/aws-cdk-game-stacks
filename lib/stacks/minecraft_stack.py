from functools import cached_property

from aws_cdk import Duration
from aws_cdk import aws_ec2 as ec2
from aws_cdk import aws_ecs as ecs
from aws_cdk import aws_route53 as route53
from constructs import Construct

from lib.aws_common.ecs import build_container
from lib.aws_common.iam import ec2_instances_read, ecs_cluster_read_policy
from lib.config import GameProperties
from lib.config.minecraft import EMAIL
from lib.stacks.game_stack import GameStack


class MinecraftStack(GameStack):
    def __init__(self, scope: Construct, props: GameProperties, **kwargs) -> None:
        """Minecraft Stack"""
        super().__init__(scope, props, **kwargs)
        self.minecraft_srv_record()
        self.traefik_container()

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
                f"traefik.http.routers.dynmap-https.rule": f"Host(`{self.fqdn}`)",
                "traefik.http.services.dynmap-https.loadbalancer.server.port": "8123",
                "traefik.http.routers.dynmap-https.entrypoints": "websecure",
                "traefik.http.routers.dynmap-https.service": "dynmap-https",
                "traefik.http.routers.dynmap-https.tls": "true",
                "traefik.http.routers.dynmap-https.tls.certresolver": "le",
            },
        )
        for port in self.props.tcp_ports:
            container.add_port_mappings(
                ecs.PortMapping(container_port=port, host_port=port, protocol=ecs.Protocol.TCP)
            )

        for port in self.props.udp_ports:
            container.add_port_mappings(
                ecs.PortMapping(container_port=port, host_port=port, protocol=ecs.Protocol.UDP)
            )

        container.add_mount_points(
            ecs.MountPoint(
                container_path=self.props.container_path,
                source_volume=self.efs_volume.name,
                read_only=False,
            )
        )

    def minecraft_srv_record(self) -> route53.SrvRecord:
        record = route53.SrvRecord(
            self,
            "MinecraftSrvRecord",
            values=[route53.SrvRecordValue(host_name=self.fqdn, port=25565, priority=0, weight=0)],
            zone=self.hosted_zone,
            record_name=f"_minecraft._tcp.{self.fqdn}",
            ttl=Duration.seconds(60),
        )
        return record

    def traefik_container(self):
        """Use a container for reverse proxy to Minecraft plugins"""
        container = build_container(
            task=self.task,
            name="Traefik",
            container_image="traefik:v2.8",
            cpu=128,
            memory_limit_mib=128,
            command=[
                f"--providers.ecs.clusters={self.cluster.cluster_name}",
                f"--providers.ecs.region={self.region}",
                "--entrypoints.web.address=:80",
                "--entrypoints.websecure.address=:443",
                "--entrypoints.http-alt.address=:8080",
                "--certificatesresolvers.le.acme.httpchallenge.entrypoint=web",
                f"--certificatesresolvers.le.acme.email={EMAIL}",
                # "--certificatesresolvers.le.acme.storage=/certs/acme.json",
                "--serverstransport.insecureskipverify=true",
                "--accesslog=true",
                "--log.level=DEBUG",
            ],
        )
        ports = [80, 443, 8080]
        for port in ports:
            container.add_port_mappings(
                ecs.PortMapping(container_port=port, host_port=port, protocol=ecs.Protocol.TCP)
            )
            self.instance_security_group.add_ingress_rule(
                ec2.Peer.any_ipv4(),
                ec2.Port.tcp(port),
                f"Traefik port tcp/{port} from anywhere",
            )

        self.task.add_to_task_role_policy(ec2_instances_read(resources=["*"]))
        self.task.add_to_task_role_policy(ecs_cluster_read_policy(resources=["*"]))
