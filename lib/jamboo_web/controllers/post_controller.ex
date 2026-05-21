defmodule JambooWeb.PostController do
  use JambooWeb, :controller
  alias Jamboo.Content
  alias Jamboo.Content.Post
  alias Jamboo.Comments

  def index(conn, _params) do
    posts = Content.list_posts()
    render(conn, :index, posts: posts)
  end

  def show(conn, %{"id" => id}) do
    post = Content.get_post!(id)
    comments = Comments.list_comments_for_post(post.id)
    render(conn, :show, post: post, comments: comments)
  end

  def new(conn, _params) do
    form = Content.change_post(%Post{}) |> to_form()
    render(conn, :new, form: form)
  end

  def create(conn, %{"post" => post_params}) do
    case Content.create_post(post_params) do
      {:ok, post} ->
        conn
        |> put_flash(:info, "Пост создан!")
        |> redirect(to: ~p"/posts/#{post}")

      {:error, changeset} ->
        render(conn, :new, form: to_form(changeset))
    end
  end

  def edit(conn, %{"id" => id}) do
    post = Content.get_post!(id)
    form = Content.change_post(post) |> to_form()
    render(conn, :edit, post: post, form: form)
  end

  def update(conn, %{"id" => id, "post" => post_params}) do
    post = Content.get_post!(id)

    case Content.update_post(post, post_params) do
      {:ok, post} ->
        conn
        |> put_flash(:info, "Пост обновлён!")
        |> redirect(to: ~p"/posts/#{post}")

      {:error, changeset} ->
        render(conn, :edit, post: post, form: to_form(changeset))
    end
  end

  def delete(conn, %{"id" => id}) do
    post = Content.get_post!(id)
    {:ok, _} = Content.delete_post(post)
    conn
    |> put_flash(:info, "Пост удалён!")
    |> redirect(to: ~p"/")
  end

  # HTMX голосование
  def upvote(conn, %{"id" => id}) do
    {:ok, post} = Content.upvote(id)

    html =
      JambooWeb.PostHTML.render_post_vote(%{post: post})
      |> Phoenix.HTML.Safe.to_iodata()

    conn
    |> put_resp_header("content-type", "text/html; charset=utf-8")
    |> send_resp(200, html)
  end

  def downvote(conn, %{"id" => id}) do
    {:ok, post} = Content.downvote(id)

    html =
      JambooWeb.PostHTML.render_post_vote(%{post: post})
      |> Phoenix.HTML.Safe.to_iodata()

    conn
    |> put_resp_header("content-type", "text/html; charset=utf-8")
    |> send_resp(200, html)
  end
end