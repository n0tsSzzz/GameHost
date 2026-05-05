from collections.abc import AsyncIterator

from gamehost_node.config import Settings, get_settings
from gamehost_node.deps import get_docker_ops
from gamehost_node.main import create_app
from gamehost_node.schemas import ContainerCreateRequest, ContainerResponse
from httpx import ASGITransport, AsyncClient


class FakeDockerOps:
    async def create_container(self, payload: ContainerCreateRequest) -> ContainerResponse:
        return ContainerResponse(
            id="container-1",
            name=payload.name,
            status="created",
            host_ports={"25565": 32768},
        )

    async def start_container(self, container_id: str) -> ContainerResponse:
        return ContainerResponse(id=container_id, name="minecraft", status="running")

    async def stop_container(self, container_id: str) -> ContainerResponse:
        return ContainerResponse(id=container_id, name="minecraft", status="exited")

    async def restart_container(self, container_id: str) -> ContainerResponse:
        return ContainerResponse(id=container_id, name="minecraft", status="running")

    async def delete_container(self, container_id: str) -> None:
        return None

    async def inspect_container(self, container_id: str) -> ContainerResponse:
        return ContainerResponse(id=container_id, name="minecraft", status="running")

    async def stream_logs(self, container_id: str) -> AsyncIterator[str]:
        yield f"{container_id}: booting"

    async def tail_logs(self, container_id: str, tail: int) -> list[str]:
        return [f"{container_id}: tail={tail}"]

    async def exec_container(self, container_id: str, command: list[str]) -> str:
        return f"{container_id}: {' '.join(command)}"


async def test_container_endpoints_require_api_key() -> None:
    app = create_app()
    app.dependency_overrides[get_docker_ops] = lambda: FakeDockerOps()
    app.dependency_overrides[get_settings] = lambda: Settings(
        node_agent_api_key="dev-node-agent-key",
    )

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/containers/container-1")

    assert response.status_code == 401


async def test_container_lifecycle_with_api_key() -> None:
    app = create_app()
    app.dependency_overrides[get_docker_ops] = lambda: FakeDockerOps()
    app.dependency_overrides[get_settings] = lambda: Settings(
        node_agent_api_key="dev-node-agent-key",
    )
    headers = {"Authorization": "Bearer dev-node-agent-key"}

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        create_response = await client.post(
            "/containers",
            headers=headers,
            json={"name": "minecraft", "image": "itzg/minecraft-server:latest"},
        )
        inspect_response = await client.get("/containers/container-1", headers=headers)
        start_response = await client.post("/containers/container-1/start", headers=headers)
        exec_response = await client.post(
            "/containers/container-1/exec",
            headers=headers,
            json={"command": ["true"]},
        )
        logs_response = await client.get("/containers/container-1/logs?tail=25", headers=headers)

    assert create_response.status_code == 201
    assert inspect_response.json()["status"] == "running"
    assert start_response.json()["status"] == "running"
    assert exec_response.json()["output"] == "container-1: true"
    assert logs_response.json()["lines"] == ["container-1: tail=25"]
