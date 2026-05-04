"use client";

import { useQuery } from "@tanstack/react-query";
import { AppNav } from "@/components/app-nav";
import { StatusPill } from "@/components/status-pill";
import { apiFetch, type NodeSummary, type TemplateSummary } from "@/lib/api";

interface AuditLog {
  id: string;
  action: string;
  targetType: string;
  targetId: string;
}

export default function AdminPage() {
  const { data: nodes } = useQuery({ queryKey: ["nodes"], queryFn: () => apiFetch<NodeSummary[]>("/nodes"), retry: false });
  const { data: templates } = useQuery({ queryKey: ["templates"], queryFn: () => apiFetch<TemplateSummary[]>("/templates"), retry: false });
  const { data: audit } = useQuery({ queryKey: ["audit"], queryFn: () => apiFetch<AuditLog[]>("/audit"), retry: false });

  return (
    <>
      <AppNav />
      <main className="mx-auto grid w-full max-w-6xl gap-6 px-6 py-6">
        <h1 className="text-2xl font-semibold">Admin</h1>
        <section className="grid gap-4 lg:grid-cols-2">
          <div className="rounded-md border border-border p-4">
            <h2 className="mb-3 font-medium">Nodes</h2>
            {(nodes ?? []).map((node) => (
              <div key={node.id} className="flex items-center justify-between border-t border-border py-2 text-sm">
                <span>{node.name}</span>
                <StatusPill value={node.status} />
              </div>
            ))}
          </div>
          <div className="rounded-md border border-border p-4">
            <h2 className="mb-3 font-medium">Templates</h2>
            {(templates ?? []).map((template) => (
              <div key={template.id} className="border-t border-border py-2 text-sm">
                <p className="font-medium">{template.displayName}</p>
                <p className="text-muted-foreground">{template.dockerImage}</p>
              </div>
            ))}
          </div>
        </section>
        <section className="rounded-md border border-border p-4">
          <h2 className="mb-3 font-medium">Audit</h2>
          {(audit ?? []).map((entry) => (
            <div key={entry.id} className="grid grid-cols-[180px_120px_1fr] border-t border-border py-2 text-sm">
              <span>{entry.action}</span>
              <span className="text-muted-foreground">{entry.targetType}</span>
              <span className="text-muted-foreground">{entry.targetId}</span>
            </div>
          ))}
        </section>
      </main>
    </>
  );
}
