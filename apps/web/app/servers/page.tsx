"use client";

import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import { Plus, RotateCw } from "lucide-react";
import { AppNav } from "@/components/app-nav";
import { StatusPill } from "@/components/status-pill";
import { Button } from "@/components/ui/button";
import { apiFetch, type ServerSummary } from "@/lib/api";

const fallbackServers: ServerSummary[] = [
  { id: "preview-minecraft", name: "Friday Minecraft", status: "running", host: "mc.local", port: 25565 },
  { id: "preview-valheim", name: "Valheim crew", status: "stopped", host: null, port: null },
];

export default function ServersPage() {
  const { data, refetch, isFetching } = useQuery({
    queryKey: ["servers"],
    queryFn: () => apiFetch<ServerSummary[]>("/servers"),
    retry: false,
  });
  const servers = data ?? fallbackServers;

  return (
    <>
      <AppNav />
      <main className="mx-auto grid w-full max-w-6xl gap-6 px-6 py-6">
        <section className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-semibold">Servers</h1>
            <p className="text-sm text-muted-foreground">Minecraft, Valheim, Terraria, CS2 and Rust instances</p>
          </div>
          <div className="flex gap-2">
            <Button variant="secondary" onClick={() => void refetch()} title="Refresh">
              <RotateCw className={isFetching ? "h-4 w-4 animate-spin" : "h-4 w-4"} />
            </Button>
            <Button>
              <Plus className="mr-2 h-4 w-4" />
              Create
            </Button>
          </div>
        </section>
        <section className="overflow-hidden rounded-md border border-border">
          <div className="grid grid-cols-[1fr_140px_180px] border-b border-border px-4 py-2 text-xs font-medium text-muted-foreground">
            <span>Name</span>
            <span>Status</span>
            <span>Address</span>
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
        </section>
      </main>
    </>
  );
}
