"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import { Plus, RotateCw } from "lucide-react";
import { useEffect, useState } from "react";
import { AppNav } from "@/components/app-nav";
import { StatusPill } from "@/components/status-pill";
import { Button } from "@/components/ui/button";
import {
  ApiError,
  apiFetch,
  getAccessToken,
  refreshAccessToken,
  type ServerSummary,
  type TaskAccepted,
  type TemplateSummary,
} from "@/lib/api";
import { gameConfigToEnv, getGameConfigSchema, initialGameConfigValues } from "@/lib/game-config";
import { useI18n } from "@/lib/i18n";

export default function ServersPage() {
  const { locale, t } = useI18n();
  const router = useRouter();
  const [isCreating, setIsCreating] = useState(false);
  const [serverName, setServerName] = useState("");
  const [templateId, setTemplateId] = useState("");
  const [configValues, setConfigValues] = useState<Record<string, string>>({});
  const [createError, setCreateError] = useState<string | null>(null);
  const [authReady, setAuthReady] = useState(false);
  const { data, error, refetch, isFetching } = useQuery({
    queryKey: ["servers"],
    queryFn: () => apiFetch<ServerSummary[]>("/servers"),
    retry: false,
    enabled: authReady,
  });
  const { data: templates } = useQuery({
    queryKey: ["templates"],
    queryFn: () => apiFetch<TemplateSummary[]>("/templates"),
    retry: false,
    enabled: authReady,
  });
  const servers = data ?? [];
  const selectedTemplate = templates?.find((item) => item.id === templateId);
  const configSchema = getGameConfigSchema(selectedTemplate?.slug);

  useEffect(() => {
    let isMounted = true;
    async function prepareAuth() {
      if (getAccessToken() !== null) {
        setAuthReady(true);
        return;
      }
      const refreshedAccess = await refreshAccessToken();
      if (!isMounted) {
        return;
      }
      if (refreshedAccess) {
        setAuthReady(true);
      } else {
        router.replace("/login");
      }
    }
    void prepareAuth();
    return () => {
      isMounted = false;
    };
  }, [router]);

  useEffect(() => {
    if (error instanceof ApiError && error.status === 401) {
      router.replace("/login");
    }
  }, [error, router]);

  useEffect(() => {
    if (!templateId && templates?.[0]) {
      setTemplateId(templates[0].id);
    }
  }, [templateId, templates]);

  useEffect(() => {
    if (!selectedTemplate) {
      return;
    }
    setConfigValues(initialGameConfigValues(configSchema, selectedTemplate.defaultEnv));
  }, [configSchema, selectedTemplate]);

  async function createServer(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setCreateError(null);
    const envOverrides = gameConfigToEnv(configSchema, configValues);
    try {
      const task = await apiFetch<TaskAccepted>("/servers", {
        method: "POST",
        body: JSON.stringify({
          name: serverName,
          templateId,
          envOverrides,
        }),
      });
      if (task.serverId) {
        window.localStorage.setItem(`gamehost.lastTask.${task.serverId}`, task.taskId);
      }
      setServerName("");
      setIsCreating(false);
      await refetch();
      if (task.serverId) {
        router.push(`/servers/${task.serverId}`);
      }
    } catch (err) {
      setCreateError(err instanceof Error ? err.message : t("createServerError"));
    }
  }

  return (
    <>
      <AppNav />
      <main className="mx-auto grid w-full max-w-6xl gap-6 px-6 py-6">
        <section className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-semibold">{t("servers")}</h1>
            <p className="text-sm text-muted-foreground">{t("minecraftFamily")}</p>
          </div>
          <div className="flex gap-2">
            <Button variant="secondary" onClick={() => void refetch()} title={t("refresh")}>
              <RotateCw className={isFetching ? "h-4 w-4 animate-spin" : "h-4 w-4"} />
            </Button>
            <Button onClick={() => setIsCreating((value) => !value)}>
              <Plus className="mr-2 h-4 w-4" />
              {t("create")}
            </Button>
          </div>
        </section>
        {isCreating ? (
          <form onSubmit={createServer} className="grid gap-4 rounded-md border border-border p-4">
            <div className="grid gap-3 md:grid-cols-[1fr_1fr_auto]">
              <input
                className="h-10 rounded-md border border-border bg-background px-3 text-sm"
                value={serverName}
                onChange={(event) => setServerName(event.target.value)}
                placeholder={t("serverName")}
                required
              />
              <select
                className="h-10 rounded-md border border-border bg-background px-3 text-sm"
                value={templateId}
                onChange={(event) => setTemplateId(event.target.value)}
                aria-label={t("template")}
                required
              >
                {(templates ?? []).map((template) => (
                  <option key={template.id} value={template.id}>
                    {template.displayName}
                  </option>
                ))}
              </select>
              <Button disabled={!serverName || !templateId}>{t("createServer")}</Button>
            </div>
            {configSchema ? (
              <div className="grid gap-3 md:grid-cols-2">
                <div className="md:col-span-2">
                  <h2 className="text-sm font-medium">{configSchema.title[locale]}</h2>
                  <p className="mt-1 text-xs text-muted-foreground">{configSchema.hint[locale]}</p>
                </div>
                {configSchema.fields.map((field) => (
                  <label
                    key={field.env}
                    className={field.type === "checkbox" ? "flex h-10 items-center gap-2 text-sm" : "grid gap-1 text-sm"}
                  >
                    {field.type !== "checkbox" ? (
                      <span className="text-muted-foreground">{field.label[locale]}</span>
                    ) : null}
                    {field.type === "select" ? (
                      <select
                        className="h-10 rounded-md border border-border bg-background px-3 text-sm"
                        value={configValues[field.env] ?? field.defaultValue}
                        onChange={(event) =>
                          setConfigValues((current) => ({ ...current, [field.env]: event.target.value }))
                        }
                        aria-label={field.label[locale]}
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
                        onChange={(event) =>
                          setConfigValues((current) => ({ ...current, [field.env]: event.target.value }))
                        }
                        placeholder={field.placeholder ?? field.label[locale]}
                      />
                    ) : null}
                    {field.type === "checkbox" ? (
                      <>
                        <input
                          checked={(configValues[field.env] ?? field.defaultValue).toLowerCase() !== "false"}
                          type="checkbox"
                          onChange={(event) =>
                            setConfigValues((current) => ({
                              ...current,
                              [field.env]: event.target.checked ? "true" : "false",
                            }))
                          }
                        />
                        <span>{field.label[locale]}</span>
                      </>
                    ) : null}
                  </label>
                ))}
              </div>
            ) : null}
            {createError ? <p className="text-sm text-red-500">{createError}</p> : null}
          </form>
        ) : null}
        <section className="overflow-hidden rounded-md border border-border">
          <div className="grid grid-cols-[1fr_140px_180px] border-b border-border px-4 py-2 text-xs font-medium text-muted-foreground">
            <span>{t("name")}</span>
            <span>{t("status")}</span>
            <span>{t("address")}</span>
          </div>
          {servers.map((server) => (
            <Link
              key={server.id}
              href={`/servers/${server.id}`}
              className="grid grid-cols-[1fr_140px_180px] items-center px-4 py-3 text-sm hover:bg-muted"
            >
              <span className="font-medium">{server.name}</span>
              <StatusPill value={server.status} />
              <span className="text-muted-foreground">
                {server.host && server.port ? `${server.host}:${server.port}` : "-"}
              </span>
            </Link>
          ))}
          {servers.length === 0 ? (
            <div className="px-4 py-8 text-sm text-muted-foreground">{t("emptyServers")}</div>
          ) : null}
        </section>
      </main>
    </>
  );
}
