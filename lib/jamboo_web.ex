defmodule JambooWeb do
  @moduledoc """
  Основной модуль веб-части приложения Jamboo.
  """

  def static_paths do
    ~w(assets fonts images favicon.ico robots.txt)
  end

  def controller do
    quote do
      use Phoenix.Controller,
        formats: [:html, :json],
        layouts: [html: JambooWeb.Layouts]

      import Plug.Conn
      import JambooWeb.Gettext

      unquote(verified_routes())
    end
  end

  def html do
    quote do
      use Phoenix.Component

      import Phoenix.Component
      import Phoenix.HTML
      import JambooWeb.Gettext
      import JambooWeb.CoreComponents

      alias JambooWeb.Layouts

      unquote(verified_routes())
    end
  end

  def router do
    quote do
      use Phoenix.Router

      import Plug.Conn
      import Phoenix.Controller
	  import Phoenix.LiveView.Router
    end
  end

  def layouts do
    quote do
      use Phoenix.Component

      import Phoenix.Component
      import JambooWeb.CoreComponents

      unquote(verified_routes())
    end
  end

  def verified_routes do
    quote do
      use Phoenix.VerifiedRoutes,
        endpoint: JambooWeb.Endpoint,
        router: JambooWeb.Router
    end
  end

  defmacro __using__(which) when is_atom(which) do
    apply(__MODULE__, which, [])
  end
end