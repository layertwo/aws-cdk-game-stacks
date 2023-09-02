from functools import cached_property

from aws_cdk import Aws, Duration
from aws_cdk import aws_ec2 as ec2
from aws_cdk import aws_ecs as ecs
from aws_cdk import aws_iam as iam
from aws_cdk import aws_route53 as route53
from constructs import Construct

from lib.aws_common.ecs import build_container
from lib.aws_common.iam import ec2_instances_read, ecs_cluster_read_policy
from lib.config.minecraft import EMAIL


class TraefikService(Construct):
    def __init__(
        self, scope: Construct, id: str, cluster: ecs.Cluster, security_group: ec2.SecurityGroup
    ) -> None:
        """Traefik service"""
        super().__init__(scope, id)
        self.cluster = cluster
        self.security_group = security_group
        self.create_service()

    @cached_property
    def task(self) -> ecs.Ec2TaskDefinition:
        """
        Create an ECS task for the specified
        """
        task = ecs.Ec2TaskDefinition(
            self,
            "TraefikTaskDef",
            # volumes=[self.ecs_volume],
            network_mode=ecs.NetworkMode.HOST,
        )
        task.add_to_task_role_policy(ec2_instances_read(resources=["*"]))
        task.add_to_task_role_policy(ecs_cluster_read_policy(resources=["*"]))
        return task

    def create_service(self) -> ecs.Ec2Service:
        """Create a Ec2Service from Traefik"""
        name = "TraefikEc2Service"
        self.build_container()
        service = ecs.Ec2Service(
            self,
            name,
            service_name=name,
            cluster=self.cluster,
            task_definition=self.task,
            desired_count=1,
            min_healthy_percent=0,
        )
        service.auto_scale_task_count(max_capacity=1, min_capacity=1)
        return service

    def build_container(self):
        """Use a container for reverse proxy to Minecraft plugins"""
        container = build_container(
            task=self.task,
            name="Traefik",
            container_image="traefik:v2.10",
            cpu=128,
            memory_limit_mib=128,
            command=[
                f"--providers.ecs.clusters={self.cluster.cluster_name}",
                f"--providers.ecs.region={Aws.REGION}",
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
            self.security_group.add_ingress_rule(
                ec2.Peer.any_ipv4(),
                ec2.Port.tcp(port),
                f"Traefik port tcp/{port} from anywhere",
            )

        return container
