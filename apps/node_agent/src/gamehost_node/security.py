from secrets import compare_digest
from typing import Annotated

from fastapi import Depends, HTTPException, Request, status

from gamehost_node.config import Settings, get_settings

SettingsDep = Annotated[Settings, Depends(get_settings)]


async def require_api_key(request: Request, settings: SettingsDep) -> None:
    authorization = request.headers.get("authorization", "")
    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not compare_digest(token, settings.node_agent_api_key):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid API key")
