from collections.abc import AsyncIterator
from typing import Any, cast

import anyio
import docker
from docker.models.containers import Container

from gamehost_node.schemas import ContainerCreateRequest, ContainerResponse


class DockerOps:
    def __init__(self) -> None:
        self._client = docker.from_env()

    async def create_container(self, payload: ContainerCreateRequest) -> ContainerResponse:
        def create() -> ContainerResponse:
            host_config: dict[str, Any] = {}
            if payload.mem_limit_mb is not None:
                host_config["mem_limit"] = f"{payload.mem_limit_mb}m"
            if payload.cpu_limit is not None:
                host_config["nano_cpus"] = int(payload.cpu_limit * 1_000_000_000)
            container = self._client.containers.create(
                image=payload.image,
                name=payload.name,
                environment=payload.env,
                ports=payload.ports,
                volumes=payload.volumes,
                detach=True,
                read_only=payload.read_only,
                cap_drop=["ALL"],
                **host_config,
            )
            return _to_response(container)

        return await anyio.to_thread.run_sync(create)

    async def start_container(self, container_id: str) -> ContainerResponse:
        return await self._with_container(container_id, lambda container: container.start())

    async def stop_container(self, container_id: str) -> ContainerResponse:
        return await self._with_container(container_id, lambda container: container.stop())

    async def restart_container(self, container_id: str) -> ContainerResponse:
        return await self._with_container(container_id, lambda container: container.restart())

    async def delete_container(self, container_id: str) -> None:
        def delete() -> None:
            container = self._client.containers.get(container_id)
            container.remove(force=True)

        await anyio.to_thread.run_sync(delete)

    async def inspect_container(self, container_id: str) -> ContainerResponse:
        def inspect() -> ContainerResponse:
            container = self._client.containers.get(container_id)
            container.reload()
            return _to_response(container)

        return await anyio.to_thread.run_sync(inspect)

    async def stream_logs(self, container_id: str) -> AsyncIterator[str]:
        def read_logs() -> list[bytes]:
            container = self._client.containers.get(container_id)
            return list(container.logs(stream=True, follow=False, tail=200))

        for line in await anyio.to_thread.run_sync(read_logs):
            yield line.decode("utf-8", errors="replace").rstrip("\n")

    async def exec_container(self, container_id: str, command: list[str]) -> str:
        def execute() -> str:
            container = self._client.containers.get(container_id)
            result = container.exec_run(command)
            output = result.output
            if isinstance(output, bytes):
                return output.decode("utf-8", errors="replace")
            return str(output)

        return await anyio.to_thread.run_sync(execute)

    async def _with_container(self, container_id: str, action: Any) -> ContainerResponse:
        def run() -> ContainerResponse:
            container = self._client.containers.get(container_id)
            action(container)
            container.reload()
            return _to_response(container)

        return await anyio.to_thread.run_sync(run)


def _to_response(container: Container) -> ContainerResponse:
    state = cast(dict[str, Any], container.attrs).get("State", {})
    return ContainerResponse(
        id=str(container.id),
        name=str(container.name),
        status=str(cast(dict[str, Any], state).get("Status", container.status)),
    )
