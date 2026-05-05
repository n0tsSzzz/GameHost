"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { UserPlus } from "lucide-react";
import { useState } from "react";
import { Button } from "@/components/ui/button";
import { setAccessToken } from "@/lib/api";
import { useI18n } from "@/lib/i18n";

export default function RegisterPage() {
  const { t } = useI18n();
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);

  async function submit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    const registerResponse = await fetch("/api/v1/auth/register", {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({ email, password }),
    });
    if (!registerResponse.ok && registerResponse.status !== 409) {
      setError(t("registrationFailed"));
      return;
    }

    const loginResponse = await fetch("/api/v1/auth/login", {
      method: "POST",
      headers: { "content-type": "application/json" },
      credentials: "include",
      body: JSON.stringify({ email, password }),
    });
    if (!loginResponse.ok) {
      setError(t("checkCredentials"));
      return;
    }
    const body = (await loginResponse.json()) as { access: string };
    setAccessToken(body.access);
    router.push("/servers");
  }

  return (
    <main className="grid min-h-screen place-items-center px-6">
      <form onSubmit={submit} className="grid w-full max-w-sm gap-4 rounded-md border border-border p-5">
        <div>
          <h1 className="text-xl font-semibold">{t("createAccount")}</h1>
          <p className="text-sm text-muted-foreground">{t("startManaging")}</p>
        </div>
        <input
          className="h-10 rounded-md border border-border bg-background px-3 text-sm"
          value={email}
          onChange={(event) => setEmail(event.target.value)}
          type="email"
          aria-label={t("email")}
          placeholder="you@example.com"
          required
        />
        <input
          className="h-10 rounded-md border border-border bg-background px-3 text-sm"
          value={password}
          onChange={(event) => setPassword(event.target.value)}
          type="password"
          aria-label={t("password")}
          placeholder={t("password")}
          required
        />
        {error ? <p className="text-sm text-red-500">{error}</p> : null}
        <Button>
          <UserPlus className="mr-2 h-4 w-4" aria-hidden="true" />
          {t("register")}
        </Button>
        <p className="text-center text-sm text-muted-foreground">
          {t("alreadyHaveAccount")}{" "}
          <Link href="/login" className="text-primary">
            {t("signInLink")}
          </Link>
        </p>
      </form>
    </main>
  );
}
