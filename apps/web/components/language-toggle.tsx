"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";

export function LanguageToggle() {
  const [locale, setLocale] = useState<"en" | "ru">("en");

  return (
    <Button
      aria-label="Toggle language"
      title="Toggle language"
      variant="secondary"
      onClick={() => setLocale(locale === "en" ? "ru" : "en")}
    >
      {locale.toUpperCase()}
    </Button>
  );
}
