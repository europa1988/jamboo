defmodule JambooWeb.Layouts do
  @moduledoc "Макеты приложения (layout-компоненты)"
  use JambooWeb, :html

  embed_templates "layouts/*"

  @doc """
  Renders the flash group.
  """
  attr :flash, :map, required: true
  attr :id, :string, default: "flash-group"

  def flash_group(assigns) do
    ~H"""
    <div id={@id}>
      <.flash kind={:info} flash={@flash} />
      <.flash kind={:error} flash={@flash} />
    </div>
    """
  end
end
