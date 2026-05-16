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

  defp assign_current_scope(conn, _opts) do
    # Placeholder plug to ensure @current_scope is always available
    # and not overwritten by manual assignments in controllers.
    # Replace with real authentication logic when ready.
    assign(conn, :current_scope, conn.assigns[:current_scope] || nil)
  end

  pipeline :api do
    plug :accepts, ["json"]
  end

  scope "/", JambooWeb do
    pipe_through :browser

    get "/", PostController, :index
    resources "/posts", PostController
    put "/posts/:id/upvote", PostController, :upvote
    put "/posts/:id/downvote", PostController, :downvote
    post "/posts/:post_id/comments", CommentController, :create
  end
end
