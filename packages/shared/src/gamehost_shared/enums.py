from enum import StrEnum


class UserRole(StrEnum):
    USER = "user"
    ADMIN = "admin"


class ServerMemberRole(StrEnum):
    VIEWER = "viewer"
    OPERATOR = "operator"


class NodeStatus(StrEnum):
    ONLINE = "online"
    OFFLINE = "offline"
    DRAIN = "drain"


class ServerStatus(StrEnum):
    PENDING = "pending"
    PROVISIONING = "provisioning"
    RUNNING = "running"
    STOPPED = "stopped"
    FAILED = "failed"
    DELETING = "deleting"


class TaskStatus(StrEnum):
    QUEUED = "queued"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"


class TaskKind(StrEnum):
    PROVISION_SERVER = "provision_server"
    START_SERVER = "start_server"
    STOP_SERVER = "stop_server"
    RESTART_SERVER = "restart_server"
    DELETE_SERVER = "delete_server"


class BackupStatus(StrEnum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
