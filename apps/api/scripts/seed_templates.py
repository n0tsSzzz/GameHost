from __future__ import annotations

import asyncio

from gamehost_api.db.base import AsyncSessionFactory
from gamehost_api.db.models import GameTemplate
from sqlalchemy import select

TEMPLATES: list[dict[str, object]] = [
    {
        "slug": "minecraft-vanilla",
        "display_name": "Minecraft Vanilla",
        "docker_image": "itzg/minecraft-server:latest",
        "default_env": {"EULA": "TRUE", "TYPE": "VANILLA"},
        "default_ports": [{"containerPort": 25565, "protocol": "tcp"}],
        "default_volumes": [{"name": "data", "path": "/data"}],
        "min_resources": {"cpu": 1, "memMb": 2048},
        "is_public": True,
    },
    {
        "slug": "valheim",
        "display_name": "Valheim",
        "docker_image": "lloesche/valheim-server:latest",
        "default_env": {},
        "default_ports": [{"containerPort": 2456, "protocol": "udp"}],
        "default_volumes": [{"name": "config", "path": "/config"}],
        "min_resources": {"cpu": 2, "memMb": 4096},
        "is_public": True,
    },
    {
        "slug": "terraria",
        "display_name": "Terraria",
        "docker_image": "ryshe/terraria:latest",
        "default_env": {},
        "default_ports": [{"containerPort": 7777, "protocol": "tcp"}],
        "default_volumes": [{"name": "world", "path": "/root/.local/share/Terraria/Worlds"}],
        "min_resources": {"cpu": 1, "memMb": 1024},
        "is_public": True,
    },
    {
        "slug": "cs2",
        "display_name": "Counter-Strike 2",
        "docker_image": "joedwards32/cs2:latest",
        "default_env": {},
        "default_ports": [{"containerPort": 27015, "protocol": "udp"}],
        "default_volumes": [{"name": "game", "path": "/home/steam/cs2-dedicated"}],
        "min_resources": {"cpu": 2, "memMb": 4096},
        "is_public": True,
    },
    {
        "slug": "rust",
        "display_name": "Rust",
        "docker_image": "didstopia/rust-server:latest",
        "default_env": {},
        "default_ports": [{"containerPort": 28015, "protocol": "udp"}],
        "default_volumes": [{"name": "steamcmd", "path": "/steamcmd/rust"}],
        "min_resources": {"cpu": 2, "memMb": 6144},
        "is_public": True,
    },
]


async def seed() -> None:
    async with AsyncSessionFactory() as session:
        for item in TEMPLATES:
            result = await session.execute(
                select(GameTemplate).where(GameTemplate.slug == str(item["slug"])),
            )
            if result.scalar_one_or_none() is None:
                session.add(GameTemplate(**item))
        await session.commit()

def main() -> None:
    asyncio.run(seed())


if __name__ == "__main__":
    main()
