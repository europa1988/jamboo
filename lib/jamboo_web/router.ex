defmodule JambooWeb.Router do
  use JambooWeb, :router

  pipeline :browser do
    plug :accepts, ["html"]
    plug :fetch_session
    plug :fetch_live_flash
    plug :put_root_layout, html: {JambooWeb.Layouts, :root}
    plug :put_secure_browser_headers
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
end
