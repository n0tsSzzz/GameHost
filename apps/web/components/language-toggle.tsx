import { Button } from "@/components/ui/button";
import { useI18n } from "@/lib/i18n";

export function LanguageToggle() {
  const { locale, setLocale, t } = useI18n();

  return (
    <Button
      aria-label={t("language")}
      title={t("language")}
      variant="secondary"
      onClick={() => setLocale(locale === "en" ? "ru" : "en")}
    >
      {locale.toUpperCase()}
    </Button>
  );
}
