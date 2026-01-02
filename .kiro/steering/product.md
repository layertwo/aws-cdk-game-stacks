# Product Overview

AWS CDK infrastructure for deploying game servers on AWS using containerized workloads.

The project provides reusable CDK stacks that deploy game servers (currently Minecraft) on ECS with EC2 instances, including:
- Auto-scaling groups with spot instances for cost optimization
- EFS storage for persistent game data with automated backups
- Optional scheduled start/stop for cost savings
- DNS automation via Route53 and Lambda
- GitHub OIDC integration for CI/CD deployments

The architecture uses a base `GameStack` class that can be extended for specific games (e.g., `MinecraftStack`), making it easy to deploy different game servers with consistent infrastructure patterns.
