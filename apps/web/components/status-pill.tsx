import { cn } from "@/lib/utils";

const tones: Record<string, string> = {
  running: "bg-emerald-500/15 text-emerald-700 dark:text-emerald-300",
  stopped: "bg-slate-500/15 text-slate-700 dark:text-slate-300",
  failed: "bg-red-500/15 text-red-700 dark:text-red-300",
  provisioning: "bg-cyan-500/15 text-cyan-700 dark:text-cyan-300",
  pending: "bg-amber-500/15 text-amber-700 dark:text-amber-300",
  deleting: "bg-rose-500/15 text-rose-700 dark:text-rose-300",
};

export function StatusPill({ value }: Readonly<{ value: string }>) {
  return (
    <span className={cn("rounded-md px-2 py-1 text-xs font-medium", tones[value] ?? tones.stopped)}>
      {value}
    </span>
  );
}
