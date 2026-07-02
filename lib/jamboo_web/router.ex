defmodule JambooWeb.Router do
  use JambooWeb, :router

  pipeline :browser do
    plug :accepts, ["html"]
    plug :fetch_session
    plug :fetch_live_flash
    plug :put_root_layout, html: {JambooWeb.Layouts, :root}
    plug :put_app_layout, html: {JambooWeb.Layouts, :app}
    plug :put_secure_browser_headers
    plug :assign_current_scope
  end

  pipeline :api do
    plug :accepts, ["json"]
  end

  scope "/", JambooWeb do
    pipe_through :browser

    get "/", PostController, :index
    post "/posts/:post_id/comments", CommentController, :create
    resources "/posts", PostController
    put "/posts/:id/upvote", PostController, :upvote
    put "/posts/:id/downvote", PostController, :downvote
  end

  defp assign_current_scope(conn, _opts) do
    # Здесь должна быть логика получения текущего пользователя из сессии.
    # Пока установим nil, чтобы избежать ошибок в макетах.
    assign(conn, :current_scope, nil)
  end
end
