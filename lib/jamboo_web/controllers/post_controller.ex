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
    comment_form = to_form(Comments.change_comment(%Jamboo.Comments.Comment{}), as: :comment)
    render(conn, :show, post: post, comments: comments, comment_form: comment_form)
  end

  def new(conn, _params) do
    form = to_form(Content.change_post(%Post{}))
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
    form = to_form(Content.change_post(post))
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

    conn
    |> put_layout(false)
    |> render("post_vote.html", post: post)
  end

  def downvote(conn, %{"id" => id}) do
    {:ok, post} = Content.downvote(id)

    conn
    |> put_layout(false)
    |> render("post_vote.html", post: post)
  end
end