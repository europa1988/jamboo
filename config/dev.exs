import Config

config :phoenix_live_view, :colocated_js,
  disable_symlink_warning: true

# Настройка БД (SQLite-файл в priv/repo)
config :jamboo, Jamboo.Repo,
  database: "priv/repo/jamboo_dev.db",
  pool_size: 10,
  show_sensitive_data_on_connection_error: true,
  log: :debug

# Параметры dev-сервера
config :jamboo, JambooWeb.Endpoint,
  # Только localhost. Если нужен доступ с других машин — меняй ip.
  http: [ip: {127, 0, 0, 1}, port: 4000],
  check_origin: false,
  code_reloader: true,
  debug_errors: true,
  secret_key_base: "3hDsuSgjWvAYYPxwXC1BB8Q8Kn9Q77KRQZkBTNn60IFYqrBogTzDjPD+fXoEw4bW",
  watchers: []

# Авто‑перезагрузка браузера при изменении файлов
config :jamboo, JambooWeb.Endpoint,
  live_reload: [
    web_console_logger: true,
    patterns: [
      # Статические файлы, кроме uploads
      ~r"priv/static/(?!uploads/).*\\.(js|css|png|jpeg|jpg|gif|svg)$",
      # Роутер, контроллеры, LiveView и компоненты
      ~r"lib/jamboo_web/router\\.ex$",
      ~r"lib/jamboo_web/(controllers|live|components)/.*\\.(ex|heex)$"
    ]
  ]

# Включаем dev-маршруты (dashboard и т.п.)
config :jamboo, dev_routes: true

# Упрощённый формат логов
config :logger, :default_formatter, format: "[$level] $message\\n"

# Глубокие стек‑трейсы только в dev
config :phoenix, :stacktrace_depth, 20

# Плаги инициализируются в рантайме — быстрее компиляция
config :phoenix, :plug_init_mode, :runtime

# Доп. отладка LiveView
config :phoenix_live_view,
  debug_heex_annotations: true,
  debug_attributes: true,
  enable_expensive_runtime_checks: true

# Tailwind 4 (standalone CLI)
config :jamboo, :tailwind,
  version: "4.1.18",
  default: [
    args: ~w(
      --config=tailwind.config.js
      --input=assets/css/app.css
      --output=priv/static/assets/app.css
    ),
    cd: File.cwd!
  ]