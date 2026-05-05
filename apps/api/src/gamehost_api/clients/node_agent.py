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

    async def tail_logs(self, node: Node, container_id: str, tail: int) -> list[str]:
        raise NotImplementedError


class NodeAgentClient:
    def __init__(self, settings: Settings) -> None:
        self._api_key = settings.node_agent_api_key
        self._timeout = settings.node_agent_timeout_seconds

    async def provision_server(self, node: Node, server: Server) -> tuple[str, str, int]:
        async with httpx.AsyncClient(base_url=node.endpoint_url, timeout=self._timeout) as client:
            default_env = await server.awaitable_attrs.template
            env = {
                **{key: str(value) for key, value in default_env.default_env.items()},
                **{key: str(value) for key, value in server.env_overrides.items()},
            }
            resources = {**default_env.min_resources, **server.resources}
            response = await client.post(
                "/containers",
                headers={"Authorization": f"Bearer {self._api_key}"},
                json={
                    "name": f"gamehost-{server.id}",
                    "image": server.template.docker_image,
                    "env": env,
                    "ports": _container_ports(server.template.default_ports),
                    "cpuLimit": resources.get("cpu"),
                    "memLimitMb": resources.get("memMb"),
                },
            )
            response.raise_for_status()
            body = response.json()
            start_response = await client.post(
                f"/containers/{body['id']}/start",
                headers={"Authorization": f"Bearer {self._api_key}"},
            )
            start_response.raise_for_status()
            started_body = start_response.json()
        port = _extract_port(server.template.default_ports)
        host_ports = (
            started_body.get("host_ports")
            or started_body.get("hostPorts")
            or body.get("host_ports")
            or body.get("hostPorts")
            or {}
        )
        if isinstance(host_ports, dict):
            published_port = host_ports.get(str(port))
            if isinstance(published_port, int):
                port = published_port
            elif isinstance(published_port, str):
                port = int(published_port)
        host = node.public_host
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
        async with httpx.AsyncClient(base_url=node.endpoint_url, timeout=self._timeout) as client:
            response = await client.request(
                method,
                path,
                headers={"Authorization": f"Bearer {self._api_key}"},
            )
            response.raise_for_status()

    async def tail_logs(self, node: Node, container_id: str, tail: int) -> list[str]:
        async with httpx.AsyncClient(base_url=node.endpoint_url, timeout=self._timeout) as client:
            response = await client.get(
                f"/containers/{container_id}/logs",
                params={"tail": tail},
                headers={"Authorization": f"Bearer {self._api_key}"},
            )
            response.raise_for_status()
            body = response.json()
        lines = body.get("lines", [])
        return [str(line) for line in lines] if isinstance(lines, list) else []


def _extract_port(default_ports: list[dict[str, object]]) -> int:
    if not default_ports:
        return 0
    value = default_ports[0].get("containerPort", 0)
    if isinstance(value, int):
        return value
    if isinstance(value, str):
        return int(value)
    return 0


def _container_ports(default_ports: list[dict[str, object]]) -> dict[str, int | None]:
    ports: dict[str, int | None] = {}
    for item in default_ports:
        raw_port = item.get("containerPort")
        if raw_port is None:
            continue
        container_port = int(raw_port) if isinstance(raw_port, str) else raw_port
        if not isinstance(container_port, int):
            continue
        protocol = str(item.get("protocol", "tcp")).lower()
        ports[f"{container_port}/{protocol}"] = None
    return ports
