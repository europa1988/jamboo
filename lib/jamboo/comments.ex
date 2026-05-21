defmodule Jamboo.Comments do
  import Ecto.Query, warn: false
  alias Jamboo.Repo
  alias Jamboo.Comments.Comment

  def list_comments_for_post(post_id) do
    post_id = String.to_integer("#{post_id}")
    from(c in Comment, where: c.post_id == ^post_id, order_by: [asc: c.inserted_at])
    |> Repo.all()
  end

  def create_comment(post_id, attrs) do
    post_id =
      case post_id do
        id when is_binary(id) -> String.to_integer(id)
        id -> id
      end

    %Comment{post_id: post_id}
    |> Comment.changeset(attrs)
    |> Repo.insert()
  end
end