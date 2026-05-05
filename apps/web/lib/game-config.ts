export type Locale = "en" | "ru";

type Localized = Record<Locale, string>;

export interface GameConfigOption {
  value: string;
  label: Localized;
}

export interface GameConfigField {
  env: string;
  type: "checkbox" | "select" | "text";
  label: Localized;
  placeholder?: string;
  defaultValue: string;
  options?: GameConfigOption[];
}

export interface GameConfigSchema {
  title: Localized;
  hint: Localized;
  fields: GameConfigField[];
}

const minecraft: GameConfigSchema = {
  title: { en: "Minecraft world", ru: "Мир Minecraft" },
  hint: {
    en: "World options for itzg/minecraft-server. Some values apply on restart; seed applies to a new world.",
    ru: "Настройки мира для itzg/minecraft-server. Часть значений применяется после рестарта; сид влияет на новый мир.",
  },
  fields: [
    {
      env: "DIFFICULTY",
      type: "select",
      label: { en: "Difficulty", ru: "Сложность" },
      defaultValue: "easy",
      options: [
        { value: "peaceful", label: { en: "Peaceful", ru: "Мирная" } },
        { value: "easy", label: { en: "Easy", ru: "Легкая" } },
        { value: "normal", label: { en: "Normal", ru: "Нормальная" } },
        { value: "hard", label: { en: "Hard", ru: "Сложная" } },
      ],
    },
    {
      env: "MODE",
      type: "select",
      label: { en: "Game mode", ru: "Режим игры" },
      defaultValue: "survival",
      options: [
        { value: "survival", label: { en: "Survival", ru: "Выживание" } },
        { value: "creative", label: { en: "Creative", ru: "Креатив" } },
        { value: "adventure", label: { en: "Adventure", ru: "Приключение" } },
        { value: "spectator", label: { en: "Spectator", ru: "Наблюдатель" } },
      ],
    },
    { env: "SEED", type: "text", label: { en: "World seed", ru: "Сид мира" }, defaultValue: "", placeholder: "8675309" },
    { env: "MOTD", type: "text", label: { en: "MOTD", ru: "MOTD" }, defaultValue: "A GameHost Minecraft server" },
    { env: "PVP", type: "checkbox", label: { en: "PvP", ru: "PvP" }, defaultValue: "true" },
  ],
};

const schemas: Record<string, GameConfigSchema> = {
  "minecraft-vanilla": minecraft,
  valheim: {
    title: { en: "Valheim world", ru: "Мир Valheim" },
    hint: {
      en: "Valheim uses a named world, visible server name, password, and optional preset.",
      ru: "Valheim использует имя мира, название сервера, пароль и опциональный preset.",
    },
    fields: [
      { env: "SERVER_NAME", type: "text", label: { en: "Server name", ru: "Название сервера" }, defaultValue: "GameHost Valheim" },
      { env: "WORLD_NAME", type: "text", label: { en: "World name", ru: "Имя мира" }, defaultValue: "Dedicated" },
      { env: "SERVER_PASS", type: "text", label: { en: "Password", ru: "Пароль" }, defaultValue: "" },
      {
        env: "PRESET",
        type: "select",
        label: { en: "World preset", ru: "Пресет мира" },
        defaultValue: "normal",
        options: [
          { value: "normal", label: { en: "Normal", ru: "Обычный" } },
          { value: "hard", label: { en: "Hard", ru: "Сложный" } },
          { value: "immersive", label: { en: "Immersive", ru: "Иммерсивный" } },
        ],
      },
    ],
  },
  terraria: {
    title: { en: "Terraria world", ru: "Мир Terraria" },
    hint: {
      en: "Terraria settings control world name, size, difficulty, and player limit.",
      ru: "Настройки Terraria управляют именем мира, размером, сложностью и лимитом игроков.",
    },
    fields: [
      { env: "WORLD_NAME", type: "text", label: { en: "World name", ru: "Имя мира" }, defaultValue: "GameHost" },
      {
        env: "WORLD_SIZE",
        type: "select",
        label: { en: "World size", ru: "Размер мира" },
        defaultValue: "2",
        options: [
          { value: "1", label: { en: "Small", ru: "Маленький" } },
          { value: "2", label: { en: "Medium", ru: "Средний" } },
          { value: "3", label: { en: "Large", ru: "Большой" } },
        ],
      },
      {
        env: "DIFFICULTY",
        type: "select",
        label: { en: "Difficulty", ru: "Сложность" },
        defaultValue: "0",
        options: [
          { value: "0", label: { en: "Classic", ru: "Классика" } },
          { value: "1", label: { en: "Expert", ru: "Эксперт" } },
          { value: "2", label: { en: "Master", ru: "Мастер" } },
        ],
      },
      { env: "MAX_PLAYERS", type: "text", label: { en: "Max players", ru: "Макс. игроков" }, defaultValue: "8" },
    ],
  },
  cs2: {
    title: { en: "CS2 match", ru: "Матч CS2" },
    hint: {
      en: "CS2 settings are server-facing match and access options.",
      ru: "Настройки CS2 относятся к матчу и доступу на сервер.",
    },
    fields: [
      { env: "SERVER_HOSTNAME", type: "text", label: { en: "Hostname", ru: "Название сервера" }, defaultValue: "GameHost CS2" },
      { env: "SRCDS_TOKEN", type: "text", label: { en: "Steam GSLT token", ru: "Steam GSLT token" }, defaultValue: "" },
      { env: "RCON_PASSWORD", type: "text", label: { en: "RCON password", ru: "RCON пароль" }, defaultValue: "" },
      {
        env: "GAME_MODE",
        type: "select",
        label: { en: "Mode", ru: "Режим" },
        defaultValue: "competitive",
        options: [
          { value: "competitive", label: { en: "Competitive", ru: "Соревновательный" } },
          { value: "casual", label: { en: "Casual", ru: "Обычный" } },
          { value: "deathmatch", label: { en: "Deathmatch", ru: "Deathmatch" } },
        ],
      },
    ],
  },
  rust: {
    title: { en: "Rust world", ru: "Мир Rust" },
    hint: {
      en: "Rust settings control visible name, seed, world size, and player cap.",
      ru: "Настройки Rust управляют названием, сидом, размером мира и лимитом игроков.",
    },
    fields: [
      { env: "SERVER_NAME", type: "text", label: { en: "Server name", ru: "Название сервера" }, defaultValue: "GameHost Rust" },
      { env: "SERVER_SEED", type: "text", label: { en: "World seed", ru: "Сид мира" }, defaultValue: "" },
      { env: "WORLD_SIZE", type: "text", label: { en: "World size", ru: "Размер мира" }, defaultValue: "3500" },
      { env: "MAX_PLAYERS", type: "text", label: { en: "Max players", ru: "Макс. игроков" }, defaultValue: "50" },
    ],
  },
};

export function getGameConfigSchema(slug: string | undefined): GameConfigSchema | null {
  return slug ? (schemas[slug] ?? null) : null;
}

export function initialGameConfigValues(
  schema: GameConfigSchema | null,
  env: Record<string, unknown> | undefined,
): Record<string, string> {
  if (!schema) {
    return {};
  }
  return Object.fromEntries(
    schema.fields.map((field) => [
      field.env,
      env?.[field.env] === undefined ? field.defaultValue : String(env[field.env]),
    ]),
  );
}

export function gameConfigToEnv(
  schema: GameConfigSchema | null,
  values: Record<string, string>,
): Record<string, string> {
  if (!schema) {
    return {};
  }
  return Object.fromEntries(
    schema.fields
      .map((field) => [field.env, values[field.env] ?? field.defaultValue] as const)
      .filter(([, value]) => value.trim().length > 0 || value === "false"),
  );
}
