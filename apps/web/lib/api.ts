export type ServerStatus = "pending" | "provisioning" | "running" | "stopped" | "failed" | "deleting";

export interface ServerSummary {
  id: string;
  name: string;
  status: ServerStatus;
  host: string | null;
  port: number | null;
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
  status: string;
  capacityCpu: number;
  capacityMemMb: number;
}

export interface TemplateSummary {
  id: string;
  slug: string;
  displayName: string;
  dockerImage: string;
}

export async function apiFetch<T>(path: string, init: RequestInit = {}): Promise<T> {
  const response = await fetch(`/api/v1${path}`, {
    ...init,
    headers: {
      "content-type": "application/json",
      ...init.headers,
    },
  });
  if (!response.ok) {
    throw new Error(`Request failed: ${response.status}`);
  }
  return (await response.json()) as T;
}
