"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { LogIn } from "lucide-react";
import { Button } from "@/components/ui/button";

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState("admin@example.com");
  const [password, setPassword] = useState("");

  async function submit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    await fetch("/api/v1/auth/login", {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({ email, password }),
    });
    router.push("/servers");
  }

  return (
    <main className="grid min-h-screen place-items-center px-6">
      <form onSubmit={submit} className="grid w-full max-w-sm gap-4 rounded-md border border-border p-5">
        <div>
          <h1 className="text-xl font-semibold">Sign in</h1>
          <p className="text-sm text-muted-foreground">GameHost operations console</p>
        </div>
        <input
          className="h-10 rounded-md border border-border bg-background px-3 text-sm"
          value={email}
          onChange={(event) => setEmail(event.target.value)}
          type="email"
          aria-label="Email"
        />
        <input
          className="h-10 rounded-md border border-border bg-background px-3 text-sm"
          value={password}
          onChange={(event) => setPassword(event.target.value)}
          type="password"
          aria-label="Password"
        />
        <Button>
          <LogIn className="mr-2 h-4 w-4" aria-hidden="true" />
          Continue
        </Button>
      </form>
    </main>
  );
}
