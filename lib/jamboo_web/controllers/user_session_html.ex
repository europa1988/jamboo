defmodule JambooWeb.UserSessionHTML do
  @moduledoc "Шаблоны HTML‑форм входа"
  use JambooWeb, :html

  # То же самое: подключаем form_for/3 и остальные хелперы
  import Phoenix.HTML.Form

  embed_templates "user_session_html/*"
end