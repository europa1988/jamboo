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

      {:error, changeset} ->
        comments = Comments.list_comments_for_post(post.id)

        conn
        |> put_flash(:error, "Ошибка при добавлении комментария")
        |> render(JambooWeb.PostHTML, :show,
          post: post,
          comments: comments,
          comment_form: to_form(changeset)
        )
    end
  end
end
