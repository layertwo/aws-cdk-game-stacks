import logging
import os
from typing import Any, Dict, List

from boto3.session import Session

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


JsonDict = Dict[str, Any]
JsonListDict = List[JsonDict]


def handler(event, context) -> None:
    """Update DNS for ECS Container"""
    session = Session()
    hostname = os.environ["HOSTNAME"]
    hosted_zone = os.environ["HOSTED_ZONE"]

    details = event["detail"]
    launch_type = details.get("launchType")
    logger.info(f"found {launch_type} event")

    # start with empty list of interfaces to look for public IP
    interfaces = []
    if launch_type == "EC2":
        instance_id = get_instance_id_from_container(
            session=session,
            cluster=details["clusterArn"],
            container_instance=details["containerInstanceArn"],
        )
        interfaces = get_interfaces_from_instance_id(session=session, instance_id=instance_id)

    elif launch_type == "FARGATE":
        eni = get_eni_id(attachments=event["detail"]["attachments"])
        interfaces = get_interfaces_from_eni(session=session, eni=eni)

    if interfaces:
        ip = get_public_ip_from_interfaces(interfaces=interfaces)
        if ip:
            domain = get_hosted_zone_domain(session=session, hosted_zone=hosted_zone)
            logger.info(f"Found and using IP {ip} for DNS record ({hostname}) in domain {domain}")
            fqdn = f"{hostname}.{domain}"
            update_dns_with_ip(
                session=session,
                hosted_zone=hosted_zone,
                fqdn=fqdn,
                ip=ip,
            )
            logger.info(f"Set {fqdn} to IP {ip} in hosted zone {hosted_zone}")
        else:
            logger.error(f"unable to set IP for {fqdn}. No public IP associations found")
    else:
        logger.error(f"unable to set IP for {fqdn}. No interfaces found.")


def get_interfaces_from_instance_id(session: Session, instance_id: str) -> Dict[str, Any]:
    """Get interfaces from Instance ID"""
    client = session.client("ec2")
    response = client.describe_instances(InstanceIds=[instance_id])
    return response["Reservations"][-1]["Instances"][-1]["NetworkInterfaces"]


def get_interfaces_from_eni(session: Session, eni: str) -> Dict[str, Any]:
    """For an ENI find the NetworkInterfaces assocations"""
    client = session.client("ec2")
    response = client.describe_network_interfaces(
        NetworkInterfaceIds=[eni],
    )
    return response["NetworkInterfaces"]


def get_public_ip_from_interfaces(interfaces: JsonListDict) -> str:
    """Iterate through interfaces and find PublicIP"""
    for n in interfaces:
        return n["Association"]["PublicIp"]


def get_instance_id_from_container(session: Session, cluster: str, container_instance: str) -> str:
    """Get Instance ID from container instance"""
    client = session.client("ecs")
    response = client.describe_container_instances(
        cluster=cluster, containerInstances=[container_instance]
    )
    return response["containerInstances"][-1]["ec2InstanceId"]


def get_eni_id(attachments: List) -> str:
    """Get ENI ID from ECS Fargate task"""
    for a in attachments:
        if a["type"] in ("ElasticNetworkInterface", "eni"):
            for d in a.get("details", []):
                if d["name"] == "networkInterfaceId":
                    return d["value"]
    return ""


def get_hosted_zone_domain(session: Session, hosted_zone: str) -> str:
    """Get hosted zone name"""
    client = session.client("route53")
    response = client.get_hosted_zone(Id=hosted_zone)
    return response["HostedZone"]["Name"]


def update_dns_with_ip(session: Session, hosted_zone: str, fqdn: str, ip: str):
    """Update A record to IP for FQDN"""
    client = session.client("route53")
    try:
        client.change_resource_record_sets(
            HostedZoneId=hosted_zone,
            ChangeBatch={
                "Changes": [
                    {
                        "Action": "UPSERT",
                        "ResourceRecordSet": {
                            "Name": fqdn,
                            "Type": "A",
                            "TTL": 60,
                            "ResourceRecords": [{"Value": ip}],
                        },
                    }
                ]
            },
        )
    except Exception as err:
        logger.error(err)
