from typing import Protocol

import httpx
from gamehost_shared.enums import TaskKind

from gamehost_api.core.config import Settings
from gamehost_api.db.models import Node, Server


class NodeAgentClientProtocol(Protocol):
    async def provision_server(self, node: Node, server: Server) -> tuple[str, str, int]:
        raise NotImplementedError

    async def run_lifecycle(self, node: Node, server: Server, kind: TaskKind) -> None:
        raise NotImplementedError


class NodeAgentClient:
    def __init__(self, settings: Settings) -> None:
        self._api_key = settings.node_agent_api_key

    async def provision_server(self, node: Node, server: Server) -> tuple[str, str, int]:
        async with httpx.AsyncClient(base_url=node.endpoint_url, timeout=30.0) as client:
            response = await client.post(
                "/containers",
                headers={"Authorization": f"Bearer {self._api_key}"},
                json={
                    "name": f"gamehost-{server.id}",
                    "image": server.template.docker_image,
                    "env": server.env_overrides,
                    "cpuLimit": server.resources.get("cpu"),
                    "memLimitMb": server.resources.get("memMb"),
                },
            )
            response.raise_for_status()
            body = response.json()
        port = _extract_port(server.template.default_ports)
        host = node.endpoint_url.removeprefix("http://").removeprefix("https://")
        return str(body["id"]), host, port

    async def run_lifecycle(self, node: Node, server: Server, kind: TaskKind) -> None:
        if server.container_id is None:
            raise ValueError("Server has no container")
        action = {
            TaskKind.START_SERVER: "start",
            TaskKind.STOP_SERVER: "stop",
            TaskKind.RESTART_SERVER: "restart",
            TaskKind.DELETE_SERVER: "",
        }[kind]
        path = f"/containers/{server.container_id}" if kind == TaskKind.DELETE_SERVER else (
            f"/containers/{server.container_id}/{action}"
        )
        method = "DELETE" if kind == TaskKind.DELETE_SERVER else "POST"
        async with httpx.AsyncClient(base_url=node.endpoint_url, timeout=30.0) as client:
            response = await client.request(
                method,
                path,
                headers={"Authorization": f"Bearer {self._api_key}"},
            )
            response.raise_for_status()


def _extract_port(default_ports: list[dict[str, object]]) -> int:
    if not default_ports:
        return 0
    value = default_ports[0].get("containerPort", 0)
    if isinstance(value, int):
        return value
    if isinstance(value, str):
        return int(value)
    return 0
