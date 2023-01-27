from typing import Any, Union

from aws_cdk import aws_ecs as ecs
from aws_cdk import aws_efs as efs
from aws_cdk import aws_logs as logs


def build_ecs_efs_volume(file_system: efs.FileSystem, name: str) -> ecs.Volume:
    """
    Create ECS volume for EFS mount
    """
    return ecs.Volume(
        name=f"{name}-volume",
        efs_volume_configuration=ecs.EfsVolumeConfiguration(
            file_system_id=file_system.file_system_id,
            root_directory="/",
            transit_encryption="ENABLED",
        ),
    )


def build_container(
    task: Union[ecs.Ec2TaskDefinition, ecs.FargateTaskDefinition],
    name: str,
    container_image: str,
    **kwargs: Any,
) -> ecs.ContainerDefinition:
    """Create a container for our image"""
    return task.add_container(
        f"{name}Container",
        image=ecs.ContainerImage.from_registry(container_image),
        essential=True,
        logging=ecs.LogDrivers.aws_logs(
            stream_prefix=name,
            log_retention=logs.RetentionDays.ONE_WEEK,
        ),
        **kwargs,
    )
