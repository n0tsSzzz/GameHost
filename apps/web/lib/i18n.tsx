"use client";

import { createContext, useContext, useEffect, useMemo, useState } from "react";

type Locale = "en" | "ru";

const messages = {
  en: {
    admin: "Admin",
    address: "Address",
    alreadyHaveAccount: "Already have an account?",
    audit: "Audit",
    backups: "Backups",
    checkCredentials: "Check email and password",
    confirmPassword: "Password",
    continue: "Continue",
    create: "Create",
    createAccount: "Create account",
    createBackup: "Create",
    difficulty: "Difficulty",
    difficultyEasy: "Easy",
    difficultyHard: "Hard",
    difficultyNormal: "Normal",
    difficultyPeaceful: "Peaceful",
    createServer: "Create server",
    createServerError: "Create failed",
    emptyAudit: "No audit events yet",
    emptyBackups: "No backups yet",
    emptyLogs: "No logs yet",
    emptyMembers: "No members yet",
    emptyNodes: "No nodes yet",
    emptyServers: "No servers yet",
    emptyTemplates: "No templates yet",
    email: "Email",
    invite: "Invite",
    language: "Language",
    logs: "Logs",
    gameMode: "Game mode",
    gameModeAdventure: "Adventure",
    gameModeCreative: "Creative",
    gameModeSpectator: "Spectator",
    gameModeSurvival: "Survival",
    mapConfig: "Map config",
    mapConfigHint: "Minecraft world settings. Existing worlds may require a restart or recreate before every value is visible in-game.",
    mapConfigSaveError: "Map config was not saved",
    mapConfigSaved: "Map config saved",
    logsWaitingForContainer: "Logs will appear after the worker provisions a container for this server.",
    members: "Members",
    minecraftFamily: "Minecraft, Valheim, Terraria, CS2 and Rust instances",
    name: "Name",
    noAccount: "No account yet?",
    noAddressYet: "No address yet",
    nodes: "Nodes",
    operationStatus: "Operation status",
    password: "Password",
    register: "Register",
    registrationFailed: "Registration failed",
    refresh: "Refresh",
    restart: "Restart",
    saveMapConfig: "Save map",
    serverDetails: "Server details",
    serverName: "Server name",
    servers: "Servers",
    serverStatusDeleting: "Delete task is queued or running. The server will disappear after cleanup.",
    serverStatusFailed: "Last lifecycle task failed. Check the task error and worker/node-agent logs.",
    serverStatusPending: "Provision task is queued. If it stays here, the worker is not processing jobs yet.",
    serverStatusProvisioning: "Worker is provisioning a container on a node.",
    serverStatusRunning: "Server is running. Logs are read from the node-agent.",
    serverStatusStopped: "Server is stopped. Start it to resume the container.",
    signIn: "Sign in",
    signInLink: "Sign in",
    start: "Start",
    startManaging: "Start managing game servers",
    status: "Status",
    stop: "Stop",
    taskError: "Task error",
    taskQueuedHint: "The API accepted the task. A worker must pick it up before Docker activity starts.",
    template: "Template",
    templates: "Templates",
    pvp: "PvP",
    worldSeed: "World seed",
  },
  ru: {
    admin: "Админ",
    address: "Адрес",
    alreadyHaveAccount: "Уже есть аккаунт?",
    audit: "Аудит",
    backups: "Бэкапы",
    checkCredentials: "Проверьте email и пароль",
    confirmPassword: "Пароль",
    continue: "Продолжить",
    create: "Создать",
    createAccount: "Создать аккаунт",
    createBackup: "Создать",
    difficulty: "Сложность",
    difficultyEasy: "Лёгкая",
    difficultyHard: "Сложная",
    difficultyNormal: "Нормальная",
    difficultyPeaceful: "Мирная",
    createServer: "Создать сервер",
    createServerError: "Не удалось создать сервер",
    emptyAudit: "Событий аудита пока нет",
    emptyBackups: "Бэкапов пока нет",
    emptyLogs: "Логов пока нет",
    emptyMembers: "Участников пока нет",
    emptyNodes: "Нод пока нет",
    emptyServers: "Серверов пока нет",
    emptyTemplates: "Шаблонов пока нет",
    email: "Email",
    invite: "Пригласить",
    language: "Язык",
    logs: "Логи",
    gameMode: "Режим игры",
    gameModeAdventure: "Приключение",
    gameModeCreative: "Креатив",
    gameModeSpectator: "Наблюдатель",
    gameModeSurvival: "Выживание",
    mapConfig: "Конфигурация карты",
    mapConfigHint: "Настройки мира Minecraft. Для уже созданного мира некоторые значения могут потребовать рестарт или пересоздание.",
    mapConfigSaveError: "Не удалось сохранить карту",
    mapConfigSaved: "Конфигурация карты сохранена",
    logsWaitingForContainer: "Логи появятся после того, как worker создаст контейнер для этого сервера.",
    members: "Участники",
    minecraftFamily: "Инстансы Minecraft, Valheim, Terraria, CS2 и Rust",
    name: "Название",
    noAccount: "Ещё нет аккаунта?",
    noAddressYet: "Адреса пока нет",
    nodes: "Ноды",
    operationStatus: "Состояние операции",
    password: "Пароль",
    register: "Зарегистрироваться",
    registrationFailed: "Не удалось зарегистрироваться",
    refresh: "Обновить",
    restart: "Перезапустить",
    saveMapConfig: "Сохранить карту",
    serverDetails: "Детали сервера",
    serverName: "Имя сервера",
    servers: "Серверы",
    serverStatusDeleting: "Задача удаления поставлена в очередь или выполняется. Сервер исчезнет после очистки.",
    serverStatusFailed: "Последняя задача завершилась с ошибкой. Проверьте ошибку задачи и логи worker/node-agent.",
    serverStatusPending: "Задача создания в очереди. Если статус не меняется, worker ещё не обрабатывает задачи.",
    serverStatusProvisioning: "Worker создаёт контейнер на ноде.",
    serverStatusRunning: "Сервер запущен. Логи читаются через node-agent.",
    serverStatusStopped: "Сервер остановлен. Запустите его, чтобы поднять контейнер.",
    signIn: "Войти",
    signInLink: "Войти",
    start: "Запустить",
    startManaging: "Начните управлять игровыми серверами",
    status: "Статус",
    stop: "Остановить",
    taskError: "Ошибка задачи",
    taskQueuedHint: "API принял задачу. Worker должен забрать её до начала действий в Docker.",
    template: "Шаблон",
    templates: "Шаблоны",
    pvp: "PvP",
    worldSeed: "Сид мира",
  },
} satisfies Record<Locale, Record<string, string>>;

type MessageKey = keyof typeof messages.en;

interface I18nContextValue {
  locale: Locale;
  setLocale: (locale: Locale) => void;
  t: (key: MessageKey) => string;
}

const I18nContext = createContext<I18nContextValue | null>(null);

export function I18nProvider({ children }: Readonly<{ children: React.ReactNode }>) {
  const [locale, setLocale] = useState<Locale>("en");
  useEffect(() => {
    const saved = window.localStorage.getItem("gamehost.locale");
    if (saved === "en" || saved === "ru") {
      setLocale(saved);
    } else if (window.navigator.language.toLowerCase().startsWith("ru")) {
      setLocale("ru");
    }
  }, []);

  const value = useMemo<I18nContextValue>(
    () => ({
      locale,
      setLocale: (nextLocale) => {
        window.localStorage.setItem("gamehost.locale", nextLocale);
        setLocale(nextLocale);
      },
      t: (key) => messages[locale][key],
    }),
    [locale],
  );

  return <I18nContext.Provider value={value}>{children}</I18nContext.Provider>;
}

export function useI18n() {
  const context = useContext(I18nContext);
  if (context === null) {
    throw new Error("useI18n must be used inside I18nProvider");
  }
  return context;
}
