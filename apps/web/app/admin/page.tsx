"use client";

import { useQuery } from "@tanstack/react-query";
import { AppNav } from "@/components/app-nav";
import { StatusPill } from "@/components/status-pill";
import { ApiError, apiFetch, type NodeSummary, type TemplateSummary } from "@/lib/api";
import { useI18n } from "@/lib/i18n";

interface AuditLog {
  id: string;
  action: string;
  targetType: string;
  targetId: string;
}

export default function AdminPage() {
  const { t } = useI18n();
  const { data: nodes, error: nodesError } = useQuery({
    queryKey: ["nodes"],
    queryFn: () => apiFetch<NodeSummary[]>("/nodes"),
    retry: false,
  });
  const { data: templates } = useQuery({
    queryKey: ["templates"],
    queryFn: () => apiFetch<TemplateSummary[]>("/templates"),
    retry: false,
  });
  const { data: audit, error: auditError } = useQuery({
    queryKey: ["audit"],
    queryFn: () => apiFetch<AuditLog[]>("/audit"),
    retry: false,
  });
  const isForbidden =
    (nodesError instanceof ApiError && nodesError.status === 403) ||
    (auditError instanceof ApiError && auditError.status === 403);

  return (
    <>
      <AppNav />
      <main className="mx-auto grid w-full max-w-6xl gap-6 px-6 py-6">
        <h1 className="text-2xl font-semibold">{t("admin")}</h1>
        {isForbidden ? (
          <section className="rounded-md border border-border p-4 text-sm text-muted-foreground">
            Admin access is required. Set `GAMEHOST_ADMIN_EMAIL` in `.env`, run seed, then sign in again.
          </section>
        ) : null}
        <section className="grid gap-4 lg:grid-cols-2">
          <div className="rounded-md border border-border p-4">
            <h2 className="mb-3 font-medium">{t("nodes")}</h2>
            {(nodes ?? []).map((node) => (
              <div key={node.id} className="flex items-center justify-between border-t border-border py-2 text-sm">
                <span>{node.name}</span>
                <StatusPill value={node.status} />
              </div>
            ))}
            {nodes?.length === 0 ? <p className="text-sm text-muted-foreground">{t("emptyNodes")}</p> : null}
          </div>
          <div className="rounded-md border border-border p-4">
            <h2 className="mb-3 font-medium">{t("templates")}</h2>
            {(templates ?? []).map((template) => (
              <div key={template.id} className="border-t border-border py-2 text-sm">
                <p className="font-medium">{template.displayName}</p>
                <p className="text-muted-foreground">{template.dockerImage}</p>
              </div>
            ))}
            {templates?.length === 0 ? <p className="text-sm text-muted-foreground">{t("emptyTemplates")}</p> : null}
          </div>
        </section>
        <section className="rounded-md border border-border p-4">
          <h2 className="mb-3 font-medium">{t("audit")}</h2>
          {(audit ?? []).map((entry) => (
            <div key={entry.id} className="grid grid-cols-[180px_120px_1fr] border-t border-border py-2 text-sm">
              <span>{entry.action}</span>
              <span className="text-muted-foreground">{entry.targetType}</span>
              <span className="text-muted-foreground">{entry.targetId}</span>
            </div>
          ))}
          {audit?.length === 0 ? <p className="text-sm text-muted-foreground">{t("emptyAudit")}</p> : null}
        </section>
      </main>
    </>
  );
}
