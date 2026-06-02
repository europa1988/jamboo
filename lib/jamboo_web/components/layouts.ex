defmodule JambooWeb.Layouts do
  @moduledoc "Макеты приложения (layout-компоненты)"
  use JambooWeb, :html

  embed_templates "layouts/*"

  @doc """
  Renders the flash group.
  """
  attr :flash, :map, required: true, doc: "the map of flash messages"
  attr :id, :string, default: "flash-group", doc: "the optional id of flash container"

  def flash_group(assigns) do
    ~H"""
    <div id={@id}>
      <.flash kind={:info} title={gettext("Успех!")} flash={@flash} />
      <.flash kind={:error} title={gettext("Ошибка!")} flash={@flash} />
      <.flash
        id="client-error"
        kind={:error}
        title={gettext("Ошибка сети")}
        phx-disconnected={show(".phx-client-error #client-error")}
        phx-connected={hide("#client-error")}
        hidden
      >
        {gettext("Попытка восстановить соединение...")}
        <.icon name="hero-arrow-path" class="ml-1 size-3 animate-spin" />
      </.flash>

      <.flash
        id="server-error"
        kind={:error}
        title={gettext("Ошибка сервера")}
        phx-disconnected={show(".phx-server-error #server-error")}
        phx-connected={hide("#server-error")}
        hidden
      >
        {gettext("Что-то пошло не так! Пожалуйста, попробуйте позже.")}
        <.icon name="hero-arrow-path" class="ml-1 size-3 animate-spin" />
      </.flash>
    </div>
    """
  end
end