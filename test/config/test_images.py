import re

from lib.config.images import MINECRAFT_IMAGE, TRAEFIK_IMAGE

GHCR_PREFIX = "ghcr.io/"


def test_traefik_image_uses_ghcr():
    assert TRAEFIK_IMAGE.startswith(GHCR_PREFIX)


def test_traefik_image_has_semver_tag():
    # expects ghcr.io/traefik/traefik:vX.Y.Z
    tag = TRAEFIK_IMAGE.split(":")[-1]
    assert re.match(r"^v\d+\.\d+\.\d+$", tag), f"Unexpected tag: {tag}"


def test_minecraft_image_uses_ghcr():
    assert MINECRAFT_IMAGE.startswith(GHCR_PREFIX)


def test_minecraft_image_has_versioned_tag():
    # expects ghcr.io/itzg/minecraft-server:YYYY.M.D-java17
    tag = MINECRAFT_IMAGE.split(":")[-1]
    assert re.match(r"^\d{4}\.\d+\.\d+-java\d+$", tag), f"Unexpected tag: {tag}"
