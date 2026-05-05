export type ServerStatus = "pending" | "provisioning" | "running" | "stopped" | "failed" | "deleting";

export interface ServerSummary {
  id: string;
  ownerId?: string;
  name: string;
  templateId?: string;
  nodeId?: string | null;
  containerId?: string | null;
  status: ServerStatus;
  host: string | null;
  port: number | null;
  envOverrides?: Record<string, unknown>;
  resources?: Record<string, unknown>;
}

export interface Backup {
  id: string;
  status: string;
  sizeBytes: number;
  createdAt: string;
}

export interface Member {
  userId: string;
  role: "viewer" | "operator";
}

export interface NodeSummary {
  id: string;
  name: string;
  endpointUrl: string;
  publicHost: string;
  status: string;
  capacityCpu: number;
  capacityMemMb: number;
}

export interface TemplateSummary {
  id: string;
  slug: string;
  displayName: string;
  dockerImage: string;
  defaultEnv?: Record<string, unknown>;
  defaultPorts?: Record<string, unknown>[];
  defaultVolumes?: Record<string, unknown>[];
  minResources?: Record<string, unknown>;
  isPublic?: boolean;
}

export interface TaskAccepted {
  taskId: string;
  serverId: string | null;
  status: string;
}

export interface TaskStatusResponse {
  id: string;
  serverId: string | null;
  kind: string;
  status: "queued" | "running" | "succeeded" | "failed";
  payload: Record<string, unknown>;
  error: string | null;
}

export interface LogsTailResponse {
  lines: string[];
}

export interface UserSummary {
  id: string;
  email: string;
  role: "user" | "admin";
  isActive: boolean;
}

export class ApiError extends Error {
  constructor(
    message: string,
    readonly status: number,
  ) {
    super(message);
  }
}

export function getAccessToken(): string | null {
  if (typeof window === "undefined") {
    return null;
  }
  return window.localStorage.getItem("gamehost.access");
}

export function setAccessToken(token: string): void {
  window.localStorage.setItem("gamehost.access", token);
}

export function clearAccessToken(): void {
  if (typeof window === "undefined") {
    return;
  }
  window.localStorage.removeItem("gamehost.access");
}

export async function refreshAccessToken(): Promise<string | null> {
  const response = await fetch("/api/v1/auth/refresh", {
    method: "POST",
    credentials: "include",
  });
  if (!response.ok) {
    clearAccessToken();
    return null;
  }
  const body = (await response.json()) as { access: string };
  setAccessToken(body.access);
  return body.access;
}

async function rawApiFetch(path: string, init: RequestInit = {}, access: string | null): Promise<Response> {
  return fetch(`/api/v1${path}`, {
    ...init,
    credentials: "include",
    headers: {
      "content-type": "application/json",
      ...(access ? { authorization: `Bearer ${access}` } : {}),
      ...init.headers,
    },
  });
}

export async function apiFetch<T>(path: string, init: RequestInit = {}): Promise<T> {
  const access = getAccessToken();
  let response = await rawApiFetch(path, init, access);
  if (response.status === 401) {
    const refreshedAccess = await refreshAccessToken();
    if (refreshedAccess) {
      response = await rawApiFetch(path, init, refreshedAccess);
    }
  }
  if (!response.ok) {
    throw new ApiError(`Request failed: ${response.status}`, response.status);
  }
  return (await response.json()) as T;
}
