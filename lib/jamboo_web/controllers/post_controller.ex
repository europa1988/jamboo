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

    render(conn, :show,
      post: post,
      comments: comments,
      form: to_form(Ecto.Changeset.change(%Comments.Comment{}), as: :comment)
    )
  end

  def new(conn, _params) do
    changeset = Content.change_post(%Post{})
    render(conn, :new, changeset: changeset)
  end

  def create(conn, %{"post" => post_params}) do
    case Content.create_post(post_params) do
      {:ok, post} ->
        conn
        |> put_flash(:info, "Пост создан!")
        |> redirect(to: ~p"/posts/#{post}")
      {:error, changeset} ->
        render(conn, :new, changeset: changeset)
    end
  end

  def edit(conn, %{"id" => id}) do
    post = Content.get_post!(id)
    changeset = Content.change_post(post)
    render(conn, :edit, post: post, changeset: changeset)
  end

  def update(conn, %{"id" => id, "post" => post_params}) do
    post = Content.get_post!(id)
    case Content.update_post(post, post_params) do
      {:ok, post} ->
        conn
        |> put_flash(:info, "Пост обновлён!")
        |> redirect(to: ~p"/posts/#{post}")
      {:error, changeset} ->
        render(conn, :edit, post: post, changeset: changeset)
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
    |> render(:post_vote, post: post)
  end

  def downvote(conn, %{"id" => id}) do
    {:ok, post} = Content.downvote(id)

    conn
    |> put_layout(false)
    |> render(:post_vote, post: post)
  end
end