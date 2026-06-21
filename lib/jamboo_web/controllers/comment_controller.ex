defmodule JambooWeb.CommentController do
  use JambooWeb, :controller
  alias Jamboo.Comments
  alias Jamboo.Content

  def create(conn, %{"post_id" => post_id, "comment" => comment_params}) do
    post = Content.get_post!(post_id)
    case Comments.create_comment(post.id, comment_params) do
      {:ok, _comment} ->
        conn
        |> put_flash(:info, "Комментарий добавлен")
        |> redirect(to: ~p"/posts/#{post}")
      {:error, _changeset} ->
        conn
        |> put_flash(:error, "Ошибка при добавлении комментария")
        |> redirect(to: ~p"/posts/#{post}")
    end
  end
end
