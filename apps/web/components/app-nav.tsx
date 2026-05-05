import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import { Gamepad2, ListTree, ShieldCheck } from "lucide-react";
import { LanguageToggle } from "@/components/language-toggle";
import { ThemeToggle } from "@/components/theme-toggle";
import { apiFetch, type UserSummary } from "@/lib/api";
import { useI18n } from "@/lib/i18n";

export function AppNav() {
  const { t } = useI18n();
  const { data: user } = useQuery({
    queryKey: ["me"],
    queryFn: () => apiFetch<UserSummary>("/auth/me"),
    retry: false,
  });
  const items = [
    { href: "/servers", label: t("servers"), icon: Gamepad2 },
    ...(user?.role === "admin" ? [{ href: "/admin", label: t("admin"), icon: ShieldCheck }] : []),
  ];

  return (
    <header className="border-b border-border">
      <div className="mx-auto flex h-14 w-full max-w-6xl items-center justify-between px-6">
        <Link href="/servers" className="flex items-center gap-2 font-semibold">
          <ListTree className="h-5 w-5 text-primary" aria-hidden="true" />
          GameHost
        </Link>
        <nav className="flex items-center gap-2">
          {items.map((item) => (
            <Link
              key={item.href}
              href={item.href}
              className="inline-flex h-9 items-center gap-2 rounded-md px-3 text-sm text-muted-foreground hover:bg-muted hover:text-foreground"
            >
              <item.icon className="h-4 w-4" aria-hidden="true" />
              {item.label}
            </Link>
          ))}
          <LanguageToggle />
          <ThemeToggle />
        </nav>
      </div>
    </header>
  );
}
