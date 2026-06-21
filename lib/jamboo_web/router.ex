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

    get "/", PostController, :index
    resources "/posts", PostController
    post "/posts/:post_id/comments", CommentController, :create
    put "/posts/:id/upvote", PostController, :upvote
    put "/posts/:id/downvote", PostController, :downvote
  end

  defp assign_current_scope(conn, _) do
    assign(conn, :current_scope, conn.assigns[:current_scope] || nil)
  end
end
