"use client";

import { useParams } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import { Play, RotateCcw, Save, Square, UserPlus } from "lucide-react";
import { AppNav } from "@/components/app-nav";
import { StatusPill } from "@/components/status-pill";
import { Button } from "@/components/ui/button";
import { apiFetch, type Backup, type Member, type ServerSummary } from "@/lib/api";

export default function ServerDetailPage() {
  const params = useParams<{ id: string }>();
  const serverId = params.id;
  const { data: server } = useQuery({
    queryKey: ["server", serverId],
    queryFn: () => apiFetch<ServerSummary>(`/servers/${serverId}`),
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

  const current = server ?? {
    id: serverId,
    name: "Friday Minecraft",
    status: "running",
    host: "mc.local",
    port: 25565,
  };

  return (
    <>
      <AppNav />
      <main className="mx-auto grid w-full max-w-6xl gap-6 px-6 py-6">
        <section className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-semibold">{current.name}</h1>
            <p className="text-sm text-muted-foreground">
              {current.host && current.port ? `${current.host}:${current.port}` : "No address yet"}
            </p>
          </div>
          <StatusPill value={current.status} />
        </section>
        <section className="flex flex-wrap gap-2">
          <Button title="Start"><Play className="mr-2 h-4 w-4" />Start</Button>
          <Button variant="secondary" title="Stop"><Square className="mr-2 h-4 w-4" />Stop</Button>
          <Button variant="secondary" title="Restart"><RotateCcw className="mr-2 h-4 w-4" />Restart</Button>
        </section>
        <section className="grid gap-4 lg:grid-cols-[1.2fr_0.8fr]">
          <div className="rounded-md border border-border">
            <div className="border-b border-border px-4 py-3 font-medium">Logs</div>
            <pre className="h-72 overflow-auto p-4 text-xs text-muted-foreground">
              {`[12:00:01] Server starting\n[12:00:08] Listening for players\n[12:01:12] Player joined`}
            </pre>
          </div>
          <div className="grid gap-4">
            <div className="rounded-md border border-border p-4">
              <div className="mb-3 flex items-center justify-between">
                <h2 className="font-medium">Backups</h2>
                <Button variant="secondary"><Save className="mr-2 h-4 w-4" />Create</Button>
              </div>
              {(backups ?? []).map((backup) => (
                <div key={backup.id} className="flex justify-between border-t border-border py-2 text-sm">
                  <span>{backup.status}</span>
                  <span className="text-muted-foreground">{backup.sizeBytes} B</span>
                </div>
              ))}
            </div>
            <div className="rounded-md border border-border p-4">
              <div className="mb-3 flex items-center justify-between">
                <h2 className="font-medium">Members</h2>
                <Button variant="secondary"><UserPlus className="mr-2 h-4 w-4" />Invite</Button>
              </div>
              {(members ?? []).map((member) => (
                <div key={member.userId} className="flex justify-between border-t border-border py-2 text-sm">
                  <span>{member.userId}</span>
                  <span className="text-muted-foreground">{member.role}</span>
                </div>
              ))}
            </div>
          </div>
        </section>
      </main>
    </>
  );
}
