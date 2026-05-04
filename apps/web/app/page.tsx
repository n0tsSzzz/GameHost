import { Server, ShieldCheck, TerminalSquare } from "lucide-react";
import { Button } from "@/components/ui/button";

const stats = [
  { label: "Servers", value: "0", icon: Server },
  { label: "Nodes", value: "0", icon: ShieldCheck },
  { label: "Tasks", value: "0", icon: TerminalSquare },
];

export default function Home() {
  return (
    <main className="mx-auto flex min-h-screen w-full max-w-6xl flex-col gap-8 px-6 py-8">
      <header className="flex items-center justify-between border-b border-border pb-4">
        <div>
          <h1 className="text-2xl font-semibold tracking-normal">GameHost</h1>
          <p className="text-sm text-muted-foreground">Server operations console</p>
        </div>
        <Button>Sign in</Button>
      </header>
      <section className="grid gap-4 md:grid-cols-3">
        {stats.map((item) => (
          <div key={item.label} className="rounded-md border border-border bg-background p-4">
            <item.icon className="mb-4 h-5 w-5 text-primary" aria-hidden="true" />
            <p className="text-sm text-muted-foreground">{item.label}</p>
            <p className="text-3xl font-semibold">{item.value}</p>
          </div>
        ))}
      </section>
      <section className="rounded-md border border-border p-5">
        <h2 className="text-lg font-medium">Server fleet</h2>
        <div className="mt-4 grid h-48 place-items-center rounded-md bg-muted text-sm text-muted-foreground">
          No servers yet
        </div>
      </section>
    </main>
  );
}
