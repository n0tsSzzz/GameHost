from typing import Annotated

from fastapi import Depends

from gamehost_node.schemas import DockerOpsProtocol

_docker_ops: DockerOpsProtocol | None = None


def get_docker_ops() -> DockerOpsProtocol:
    global _docker_ops
    if _docker_ops is None:
        from gamehost_node.docker_ops import DockerOps

        _docker_ops = DockerOps()
    if _docker_ops is None:
        raise RuntimeError("Docker operations service is not initialized")
    return _docker_ops


DockerOpsDep = Annotated[DockerOpsProtocol, Depends(get_docker_ops)]
