"use client";

import { useParams } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import { Play, RotateCcw, Save, Square, UserPlus } from "lucide-react";
import { useEffect, useMemo, useRef, useState } from "react";
import { AppNav } from "@/components/app-nav";
import { StatusPill } from "@/components/status-pill";
import { Button } from "@/components/ui/button";
import {
  apiFetch,
  type Backup,
  type LogsTailResponse,
  type Member,
  type ServerStatus,
  type ServerSummary,
  type TaskAccepted,
  type TaskStatusResponse,
  type TemplateSummary,
} from "@/lib/api";
import { gameConfigToEnv, getGameConfigSchema, initialGameConfigValues } from "@/lib/game-config";
import { useI18n } from "@/lib/i18n";

function describeStatus(status: ServerStatus, t: ReturnType<typeof useI18n>["t"]) {
  switch (status) {
    case "pending":
      return t("serverStatusPending");
    case "provisioning":
      return t("serverStatusProvisioning");
    case "running":
      return t("serverStatusRunning");
    case "stopped":
      return t("serverStatusStopped");
    case "failed":
      return t("serverStatusFailed");
    case "deleting":
      return t("serverStatusDeleting");
  }
}

export default function ServerDetailPage() {
  const { locale, t } = useI18n();
  const params = useParams<{ id: string }>();
  const serverId = params.id;
  const [lastTaskId, setLastTaskId] = useState<string | null>(null);
  const [actionError, setActionError] = useState<string | null>(null);
  const [mapDirty, setMapDirty] = useState(false);
  const [mapMessage, setMapMessage] = useState<string | null>(null);
  const [configValues, setConfigValues] = useState<Record<string, string>>({});
  const logsRef = useRef<HTMLPreElement>(null);

  const { data: server, refetch: refetchServer } = useQuery({
    queryKey: ["server", serverId],
    queryFn: () => apiFetch<ServerSummary>(`/servers/${serverId}`),
    refetchInterval: 2000,
    retry: false,
  });
  const { data: templates } = useQuery({
    queryKey: ["templates"],
    queryFn: () => apiFetch<TemplateSummary[]>("/templates"),
    retry: false,
  });
  const { data: logs } = useQuery({
    queryKey: ["server-logs", serverId, server?.containerId],
    queryFn: () => apiFetch<LogsTailResponse>(`/servers/${serverId}/logs?tail=200`),
    enabled: Boolean(server?.containerId),
    refetchInterval: 3000,
    retry: false,
  });
  const { data: task } = useQuery({
    queryKey: ["task", lastTaskId],
    queryFn: () => apiFetch<TaskStatusResponse>(`/tasks/${lastTaskId}`),
    enabled: lastTaskId !== null,
    refetchInterval: (query) => {
      const status = query.state.data?.status;
      return status === "succeeded" || status === "failed" ? false : 2000;
    },
    retry: false,
  });
  const { data: backups } = useQuery({
    queryKey: ["backups", serverId],
    queryFn: () => apiFetch<Backup[]>(`/servers/${serverId}/backups`),
    retry: false,
  });
  const { data: members } = useQuery({
    queryKey: ["members", serverId],
    queryFn: () => apiFetch<Member[]>(`/servers/${serverId}/members`),
    retry: false,
  });
  const template = templates?.find((item) => item.id === server?.templateId);
  const configSchema = getGameConfigSchema(template?.slug);

  useEffect(() => {
    setLastTaskId(window.localStorage.getItem(`gamehost.lastTask.${serverId}`));
  }, [serverId]);

  useEffect(() => {
    if (!server || mapDirty) {
      return;
    }
    setConfigValues(initialGameConfigValues(configSchema, server.envOverrides));
  }, [configSchema, mapDirty, server]);

  useEffect(() => {
    const logsElement = logsRef.current;
    if (!logsElement) {
      return;
    }
    logsElement.scrollTop = logsElement.scrollHeight;
  }, [logs?.lines, server?.containerId]);

  const address = useMemo(() => {
    if (!server?.host || !server.port) {
      return t("noAddressYet");
    }
    return `${server.host}:${server.port}`;
  }, [server, t]);

  async function enqueue(action: "start" | "stop" | "restart") {
    setActionError(null);
    try {
      const accepted = await apiFetch<TaskAccepted>(`/servers/${serverId}/${action}`, { method: "POST" });
      window.localStorage.setItem(`gamehost.lastTask.${serverId}`, accepted.taskId);
      setLastTaskId(accepted.taskId);
      await refetchServer();
    } catch (err) {
      setActionError(err instanceof Error ? err.message : "Request failed");
    }
  }

  function markMapDirty() {
    setMapDirty(true);
    setMapMessage(null);
  }

  async function saveMapConfig(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setMapMessage(null);
    const envOverrides = {
      ...(server?.envOverrides ?? {}),
      ...gameConfigToEnv(configSchema, configValues),
    };
    try {
      await apiFetch<ServerSummary>(`/servers/${serverId}`, {
        method: "PATCH",
        body: JSON.stringify({ envOverrides }),
      });
      setMapDirty(false);
      setMapMessage(t("mapConfigSaved"));
      await refetchServer();
    } catch (err) {
      setMapMessage(err instanceof Error ? err.message : t("mapConfigSaveError"));
    }
  }

  return (
    <>
      <AppNav />
      <main className="mx-auto grid w-full max-w-6xl gap-6 px-6 py-6">
        <section className="flex items-center justify-between gap-4">
          <div>
            <h1 className="text-2xl font-semibold">{server?.name ?? t("serverDetails")}</h1>
            <p className="text-sm text-muted-foreground">{address}</p>
          </div>
          {server ? <StatusPill value={server.status} /> : null}
        </section>

        {server ? (
          <section className="rounded-md border border-border p-4">
            <div className="mb-2 flex flex-wrap items-center gap-2">
              <h2 className="font-medium">{t("operationStatus")}</h2>
              <StatusPill value={task?.status ?? server.status} />
            </div>
            <p className="text-sm text-muted-foreground">{describeStatus(server.status, t)}</p>
            {lastTaskId ? (
              <p className="mt-2 text-xs text-muted-foreground">
                task: {lastTaskId}
                {task ? ` · ${task.kind} · ${task.status}` : ""}
              </p>
            ) : (
              <p className="mt-2 text-xs text-muted-foreground">{t("taskQueuedHint")}</p>
            )}
            {task?.error ? <p className="mt-2 text-sm text-red-500">{`${t("taskError")}: ${task.error}`}</p> : null}
          </section>
        ) : null}

        <section className="flex flex-wrap gap-2">
          <Button onClick={() => void enqueue("start")} title={t("start")}>
            <Play className="mr-2 h-4 w-4" />
            {t("start")}
          </Button>
          <Button variant="secondary" onClick={() => void enqueue("stop")} title={t("stop")}>
            <Square className="mr-2 h-4 w-4" />
            {t("stop")}
          </Button>
          <Button variant="secondary" onClick={() => void enqueue("restart")} title={t("restart")}>
            <RotateCcw className="mr-2 h-4 w-4" />
            {t("restart")}
          </Button>
          {actionError ? <p className="self-center text-sm text-red-500">{actionError}</p> : null}
        </section>

        <section className="grid gap-4 lg:grid-cols-[1.2fr_0.8fr]">
          <div className="rounded-md border border-border">
            <div className="border-b border-border px-4 py-3 font-medium">{t("logs")}</div>
            <pre ref={logsRef} className="h-72 overflow-auto whitespace-pre-wrap p-4 text-xs text-muted-foreground">
              {server?.containerId
                ? (logs?.lines ?? []).join("\n") || t("emptyLogs")
                : t("logsWaitingForContainer")}
            </pre>
          </div>
          <div className="grid gap-4">
            <form onSubmit={saveMapConfig} className="rounded-md border border-border p-4">
              <div className="mb-3 flex items-center justify-between gap-3">
                <div>
                  <h2 className="font-medium">{configSchema?.title[locale] ?? t("mapConfig")}</h2>
                  <p className="mt-1 text-xs text-muted-foreground">
                    {configSchema?.hint[locale] ?? t("mapConfigHint")}
                  </p>
                </div>
                <Button disabled={!mapDirty || !configSchema}>
                  <Save className="mr-2 h-4 w-4" />
                  {t("saveMapConfig")}
                </Button>
              </div>
              {configSchema ? (
                <div className="grid gap-3 sm:grid-cols-2">
                  {configSchema.fields.map((field) => (
                    <label
                      key={field.env}
                      className={
                        field.type === "checkbox" ? "flex items-center gap-2 text-sm" : "grid gap-1 text-sm"
                      }
                    >
                      {field.type !== "checkbox" ? (
                        <span className="text-muted-foreground">{field.label[locale]}</span>
                      ) : null}
                      {field.type === "select" ? (
                        <select
                          className="h-10 rounded-md border border-border bg-background px-3 text-sm"
                          value={configValues[field.env] ?? field.defaultValue}
                          onChange={(event) => {
                            markMapDirty();
                            setConfigValues((current) => ({ ...current, [field.env]: event.target.value }));
                          }}
                        >
                          {(field.options ?? []).map((option) => (
                            <option key={option.value} value={option.value}>
                              {option.label[locale]}
                            </option>
                          ))}
                        </select>
                      ) : null}
                      {field.type === "text" ? (
                        <input
                          className="h-10 rounded-md border border-border bg-background px-3 text-sm"
                          value={configValues[field.env] ?? field.defaultValue}
                          onChange={(event) => {
                            markMapDirty();
                            setConfigValues((current) => ({ ...current, [field.env]: event.target.value }));
                          }}
                          placeholder={field.placeholder ?? field.label[locale]}
                        />
                      ) : null}
                      {field.type === "checkbox" ? (
                        <>
                          <input
                            checked={(configValues[field.env] ?? field.defaultValue).toLowerCase() !== "false"}
                            type="checkbox"
                            onChange={(event) => {
                              markMapDirty();
                              setConfigValues((current) => ({
                                ...current,
                                [field.env]: event.target.checked ? "true" : "false",
                              }));
                            }}
                          />
                          <span>{field.label[locale]}</span>
                        </>
                      ) : null}
                    </label>
                  ))}
                </div>
              ) : null}
              {mapMessage ? <p className="mt-3 text-sm text-muted-foreground">{mapMessage}</p> : null}
            </form>
            <div className="rounded-md border border-border p-4">
              <div className="mb-3 flex items-center justify-between">
                <h2 className="font-medium">{t("backups")}</h2>
                <Button variant="secondary">
                  <Save className="mr-2 h-4 w-4" />
                  {t("createBackup")}
                </Button>
              </div>
              {(backups ?? []).map((backup) => (
                <div key={backup.id} className="flex justify-between border-t border-border py-2 text-sm">
                  <span>{backup.status}</span>
                  <span className="text-muted-foreground">{backup.sizeBytes} B</span>
                </div>
              ))}
              {backups?.length === 0 ? <p className="text-sm text-muted-foreground">{t("emptyBackups")}</p> : null}
            </div>
            <div className="rounded-md border border-border p-4">
              <div className="mb-3 flex items-center justify-between">
                <h2 className="font-medium">{t("members")}</h2>
                <Button variant="secondary">
                  <UserPlus className="mr-2 h-4 w-4" />
                  {t("invite")}
                </Button>
              </div>
              {(members ?? []).map((member) => (
                <div key={member.userId} className="flex justify-between border-t border-border py-2 text-sm">
                  <span>{member.userId}</span>
                  <span className="text-muted-foreground">{member.role}</span>
                </div>
              ))}
              {members?.length === 0 ? <p className="text-sm text-muted-foreground">{t("emptyMembers")}</p> : null}
            </div>
          </div>
        </section>
      </main>
    </>
  );
}
