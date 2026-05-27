defmodule JambooWeb.Layouts do
  @moduledoc "Макеты приложения (layout-компоненты)"
  use JambooWeb, :html

  embed_templates "layouts/*"

  @doc """
  Renders the flash group.
  """
  attr :flash, :map, required: true, doc: "the map of flash messages"
  attr :id, :string, default: "flash-group"

  def flash_group(assigns) do
    ~H"""
    <div id={@id}>
      <JambooWeb.CoreComponents.flash kind={:info} title="Success!" flash={@flash} />
      <JambooWeb.CoreComponents.flash kind={:error} title="Error!" flash={@flash} />
      <JambooWeb.CoreComponents.flash
        id="client-error"
        kind={:error}
        title="We can't find the internet"
        phx-disconnected={show(".phx-client-error #client-error")}
        phx-connected={hide("#client-error")}
      >
        Attempting to reconnect <JambooWeb.CoreComponents.icon name="hero-arrow-path" class="ml-1 size-3 animate-spin" />
      </JambooWeb.CoreComponents.flash>

      <JambooWeb.CoreComponents.flash
        id="server-error"
        kind={:error}
        title="Something went wrong!"
        phx-disconnected={show(".phx-server-error #server-error")}
        phx-connected={hide("#server-error")}
      >
        Hang in there while we get back on track <JambooWeb.CoreComponents.icon name="hero-arrow-path" class="ml-1 size-3 animate-spin" />
      </JambooWeb.CoreComponents.flash>
    </div>
    """
  end

  defp show(js \\ %Phoenix.LiveView.JS{}, selector) do
    Phoenix.LiveView.JS.show(js,
      to: selector,
      transition:
        {"transition-all transform ease-out duration-300", "opacity-0 translate-y-4 sm:translate-y-0 sm:scale-95",
         "opacity-100 translate-y-0 sm:scale-100"}
    )
  end

  defp hide(js \\ %Phoenix.LiveView.JS{}, selector) do
    Phoenix.LiveView.JS.hide(js,
      to: selector,
      transition:
        {"transition-all transform ease-in duration-200", "opacity-100 translate-y-0 sm:scale-100",
         "opacity-0 translate-y-4 sm:translate-y-0 sm:scale-95"}
    )
  end
end