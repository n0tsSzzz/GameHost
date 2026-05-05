from __future__ import annotations

import asyncio

from gamehost_api.core.config import get_settings
from gamehost_api.core.security import hash_refresh_token
from gamehost_api.db.base import AsyncSessionFactory
from gamehost_api.db.models import GameTemplate, Node, Server, User
from gamehost_shared.enums import NodeStatus, UserRole
from sqlalchemy import select, update

TEMPLATES: list[dict[str, object]] = [
    {
        "slug": "minecraft-vanilla",
        "display_name": "Minecraft Vanilla",
        "docker_image": "itzg/minecraft-server:latest",
        "default_env": {
            "EULA": "TRUE",
            "TYPE": "VANILLA",
            "DIFFICULTY": "easy",
            "MODE": "survival",
            "PVP": "true",
            "MOTD": "A GameHost Minecraft server",
        },
        "default_ports": [{"containerPort": 25565, "protocol": "tcp"}],
        "default_volumes": [{"name": "data", "path": "/data"}],
        "min_resources": {"cpu": 1, "memMb": 2048},
        "is_public": True,
    },
    {
        "slug": "valheim",
        "display_name": "Valheim",
        "docker_image": "lloesche/valheim-server:latest",
        "default_env": {
            "SERVER_NAME": "GameHost Valheim",
            "WORLD_NAME": "Dedicated",
            "SERVER_PASS": "change-me",
            "PRESET": "normal",
        },
        "default_ports": [{"containerPort": 2456, "protocol": "udp"}],
        "default_volumes": [{"name": "config", "path": "/config"}],
        "min_resources": {"cpu": 2, "memMb": 4096},
        "is_public": True,
    },
    {
        "slug": "terraria",
        "display_name": "Terraria",
        "docker_image": "ryshe/terraria:latest",
        "default_env": {
            "WORLD_NAME": "GameHost",
            "WORLD_SIZE": "2",
            "DIFFICULTY": "0",
            "MAX_PLAYERS": "8",
        },
        "default_ports": [{"containerPort": 7777, "protocol": "tcp"}],
        "default_volumes": [{"name": "world", "path": "/root/.local/share/Terraria/Worlds"}],
        "min_resources": {"cpu": 1, "memMb": 1024},
        "is_public": True,
    },
    {
        "slug": "cs2",
        "display_name": "Counter-Strike 2",
        "docker_image": "joedwards32/cs2:latest",
        "default_env": {
            "SERVER_HOSTNAME": "GameHost CS2",
            "SRCDS_TOKEN": "",
            "RCON_PASSWORD": "change-me",
            "GAME_MODE": "competitive",
        },
        "default_ports": [{"containerPort": 27015, "protocol": "udp"}],
        "default_volumes": [{"name": "game", "path": "/home/steam/cs2-dedicated"}],
        "min_resources": {"cpu": 2, "memMb": 4096},
        "is_public": True,
    },
    {
        "slug": "rust",
        "display_name": "Rust",
        "docker_image": "didstopia/rust-server:latest",
        "default_env": {
            "SERVER_NAME": "GameHost Rust",
            "SERVER_SEED": "",
            "WORLD_SIZE": "3500",
            "MAX_PLAYERS": "50",
        },
        "default_ports": [{"containerPort": 28015, "protocol": "udp"}],
        "default_volumes": [{"name": "steamcmd", "path": "/steamcmd/rust"}],
        "min_resources": {"cpu": 2, "memMb": 6144},
        "is_public": True,
    },
]


async def seed() -> None:
    settings = get_settings()
    public_host = settings.domain
    async with AsyncSessionFactory() as session:
        for item in TEMPLATES:
            result = await session.execute(
                select(GameTemplate).where(GameTemplate.slug == str(item["slug"])),
            )
            template = result.scalar_one_or_none()
            if template is None:
                session.add(GameTemplate(**item))
            else:
                template.default_env = {**dict(item["default_env"]), **template.default_env}
        result = await session.execute(select(Node).where(Node.name == "local-node"))
        node = result.scalar_one_or_none()
        if node is None:
            session.add(
                Node(
                    name="local-node",
                    endpoint_url="http://node-agent:8010",
                    public_host=public_host,
                    api_key_hash=hash_refresh_token(settings.node_agent_api_key),
                    capacity_cpu=4,
                    capacity_mem_mb=8192,
                    status=NodeStatus.ONLINE,
                )
            )
        else:
            node.endpoint_url = "http://node-agent:8010"
            node.public_host = public_host
            node.api_key_hash = hash_refresh_token(settings.node_agent_api_key)
            node.status = NodeStatus.ONLINE
        await session.flush()
        result = await session.execute(select(Node.id).where(Node.name == "local-node"))
        node_id = result.scalar_one()
        await session.execute(
            update(Server).where(Server.node_id == node_id).values(host=public_host),
        )
        if settings.admin_email:
            result = await session.execute(
                select(User).where(User.email == settings.admin_email.lower()),
            )
            admin = result.scalar_one_or_none()
            if admin is not None:
                admin.role = UserRole.ADMIN
        await session.commit()


def main() -> None:
    asyncio.run(seed())


if __name__ == "__main__":
    main()
