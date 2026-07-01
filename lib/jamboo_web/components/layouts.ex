defmodule JambooWeb.Layouts do
  @moduledoc "Макеты приложения (layout-компоненты)"
  use JambooWeb, :html

  embed_templates "layouts/*"

  @doc """
  Renders a group of flash messages.
  """
  attr :flash, :map, required: true, doc: "the map of flash messages"
  attr :id, :string, default: "flash-group", doc: "the optional id of flash container"

  def flash_group(assigns) do
    ~H"""
    <div id={@id}>
      <.flash kind={:info} title={gettext("Успех!")} flash={@flash} />
      <.flash kind={:error} title={gettext("Ошибка!")} flash={@flash} />
    </div>
    """
  end
end