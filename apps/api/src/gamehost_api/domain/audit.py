from gamehost_api.db.models import AuditLog
from sqlalchemy import Select, select
from sqlalchemy.ext.asyncio import AsyncSession


async def list_audit_logs(
    session: AsyncSession,
    target_type: str | None,
    target_id: str | None,
    limit: int,
) -> list[AuditLog]:
    statement: Select[tuple[AuditLog]] = select(AuditLog).order_by(AuditLog.created_at.desc())
    if target_type is not None:
        statement = statement.where(AuditLog.target_type == target_type)
    if target_id is not None:
        statement = statement.where(AuditLog.target_id == target_id)
    result = await session.execute(statement.limit(limit))
    return list(result.scalars())
