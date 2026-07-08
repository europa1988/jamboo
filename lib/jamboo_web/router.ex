defmodule JambooWeb.Router do
  use JambooWeb, :router

  pipeline :browser do
    plug :accepts, ["html"]
    plug :fetch_session
    plug :fetch_live_flash
    plug :put_root_layout, html: {JambooWeb.Layouts, :root}
    plug :put_secure_browser_headers
    plug :assign_current_scope
  end

  pipeline :api do
    plug :accepts, ["json"]
  end

  scope "/", JambooWeb do
    pipe_through :browser

    post "/posts/:post_id/comments", CommentController, :create
    get "/", PostController, :index
    resources "/posts", PostController
    put "/posts/:id/upvote", PostController, :upvote
    put "/posts/:id/downvote", PostController, :downvote
  end

  # Plug to assign current_scope to conn if it's not already assigned
  defp assign_current_scope(conn, _opts) do
    assign_new(conn, :current_scope, fn -> nil end)
  end
end