defmodule JambooWeb.Layouts do
  @moduledoc "Макеты приложения (layout-компоненты)"
  use JambooWeb, :html

  embed_templates "layouts/*"

  @doc """
  Renders the flash group.
  """
  attr :flash, :map, required: true, doc: "the merge_diff of flash messages"
  attr :id, :string, default: "flash-group", doc: "the optional id of flash container"

  def flash_group(assigns) do
    ~H"""
    <div id={@id}>
      <.flash kind={:info} title="Успех!" flash={@flash} />
      <.flash kind={:error} title="Ошибка!" flash={@flash} />
      <.flash
        id="client-error"
        kind={:error}
        title="Ошибка соединения!"
        phx-disconnected={show(".phx-client-error #client-error")}
        phx-connected={hide("#client-error")}
      >
        Попытка восстановить соединение...
      </.flash>
      <.flash
        id="server-error"
        kind={:error}
        title="Ошибка сервера!"
        phx-disconnected={show(".phx-server-error #server-error")}
        phx-connected={hide("#server-error")}
      >
        Сервер недоступен. Попробуйте позже.
      </.flash>
    </div>
    """
  end
end