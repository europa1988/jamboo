defmodule JambooWeb.UserRegistrationHTML do
  @moduledoc "Шаблоны HTML‑форм регистрации"
  use JambooWeb, :html

  # ЯВНО импортируем хелперы форм Phoenix:
  # form_for/3, label/3-4, email_input/3, password_input/3, submit/2 и т.д.
  import Phoenix.HTML.Form

  embed_templates "user_registration_html/*"
end
