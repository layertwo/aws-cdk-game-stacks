# pragma: exclude file
from functools import cached_property

from aws_cdk import Aws
from aws_cdk import aws_ec2 as ec2
from aws_cdk import aws_ecs as ecs
from aws_cdk import aws_efs as efs
from aws_cdk import aws_logs as logs
from constructs import Construct

from cdk.aws_common.iam import ec2_instances_read, ecs_cluster_read_policy
from cdk.config import ServiceType
from cdk.config.images import TRAEFIK_IMAGE
from cdk.config.minecraft import EMAIL


class TraefikService(Construct):
    def __init__(
        self,
        scope: Construct,
        id: str,
        service_type: ServiceType,
        cluster: ecs.Cluster,
        security_group: ec2.SecurityGroup,
    ) -> None:
        """Traefik service"""
        super().__init__(scope, id)
        self.cluster = cluster
        self.security_group = security_group
        self.service_type = service_type

        # need to create the EFS file_system and wait before it is used by ECS
        self.file_system = self.create_file_system()
        self.create_service()

    @cached_property
    def task(self) -> ecs.TaskDefinition:
        """
        Create an ECS task for the specified
        """
        if self.service_type == ServiceType.EC2:
            task = ecs.Ec2TaskDefinition(
                self,
                "TaskDefinition",
                volumes=[self.ecs_volume],
                network_mode=ecs.NetworkMode.HOST,
            )
        elif self.service_type == ServiceType.FARGATE:
            task = ecs.FargateTaskDefinition(
                self,
                "TaskDefinition",
                cpu=256,
                volumes=[self.ecs_volume],
            )
        task.add_to_task_role_policy(ec2_instances_read(resources=["*"]))
        task.add_to_task_role_policy(ecs_cluster_read_policy(resources=["*"]))
        self.build_container(task)
        return task

    def create_service(self) -> ecs.BaseService:
        """Create service for Traefik"""
        name = "Service"
        if self.service_type == ServiceType.EC2:
            service = ecs.Ec2Service(
                self,
                name,
                service_name=name,
                cluster=self.cluster,
                task_definition=self.task,
                desired_count=1,
                min_healthy_percent=0,
            )
        elif self.service_type == ServiceType.FARGATE:
            service = ecs.FargateService(
                self,
                name,
                service_name=name,
                cluster=self.cluster,
                task_definition=self.task,
                desired_count=1,
                min_healthy_percent=0,
                assign_public_ip=True,
            )
        service.auto_scale_task_count(max_capacity=1, min_capacity=1)
        service.node.add_dependency(self.file_system)
        return service

    def build_container(self, task: ecs.TaskDefinition):
        """Use a container for reverse proxy to Minecraft plugins"""
        container = task.add_container(
            "Container",
            image=ecs.ContainerImage.from_registry(TRAEFIK_IMAGE),
            essential=True,
            logging=ecs.LogDrivers.aws_logs(
                stream_prefix="Traefik",
                log_retention=logs.RetentionDays.ONE_WEEK,
            ),
            cpu=256,
            memory_limit_mib=512,
            command=[
                f"--providers.ecs.clusters={self.cluster.cluster_name}",
                f"--providers.ecs.region={Aws.REGION}",
                "--entrypoints.web.address=:80",
                "--entrypoints.websecure.address=:443",
                "--entrypoints.http-alt.address=:8080",
                "--certificatesresolvers.le.acme.httpchallenge.entrypoint=web",
                f"--certificatesresolvers.le.acme.email={EMAIL}",
                "--certificatesresolvers.le.acme.storage=/certs/acme.json",
                "--serverstransport.insecureskipverify=true",
                "--accesslog=true",
                "--log.level=DEBUG",
                "--log.format=json",
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

        container.add_mount_points(
            ecs.MountPoint(
                container_path="/certs",
                source_volume=self.ecs_volume.name,
                read_only=False,
            )
        )

        return container

    def create_file_system(self) -> efs.FileSystem:
        name = "TraefikWebEfs"
        file_system = efs.FileSystem(
            self,
            name,
            vpc=self.cluster.vpc,
            lifecycle_policy=efs.LifecyclePolicy.AFTER_7_DAYS,
            out_of_infrequent_access_policy=efs.OutOfInfrequentAccessPolicy.AFTER_1_ACCESS,
            performance_mode=efs.PerformanceMode.GENERAL_PURPOSE,
            throughput_mode=efs.ThroughputMode.ELASTIC,
            security_group=self.efs_security_group,
        )
        file_system.add_access_point(name, path="/")
        return file_system

    @cached_property
    def ecs_volume(self) -> ecs.Volume:
        """
        Create an efs volume to mount on a container
        """
        return ecs.Volume(
            name="TraefikWebVolume",
            efs_volume_configuration=ecs.EfsVolumeConfiguration(
                file_system_id=self.file_system.file_system_id,
                root_directory="/",
                transit_encryption="ENABLED",
            ),
        )

    @cached_property
    def efs_security_group(self) -> ec2.SecurityGroup:
        """Create game security group with ports from GameProperties"""
        sg = ec2.SecurityGroup(
            self,
            "EfsSecurityGroup",
            vpc=self.cluster.vpc,
            allow_all_outbound=True,
        )

        sg.add_ingress_rule(
            ec2.Peer.security_group_id(self.security_group.security_group_id),
            ec2.Port.tcp(2049),
        )
        return sg
