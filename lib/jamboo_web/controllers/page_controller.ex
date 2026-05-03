defmodule JambooWeb.PageController do
  use JambooWeb, :controller

  def home(conn, _params) do
    render(conn, :home)
  end
end
