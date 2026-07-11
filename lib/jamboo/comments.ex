defmodule Jamboo.Comments do
  import Ecto.Query, warn: false
  alias Jamboo.Repo
  alias Jamboo.Comments.Comment

  def list_comments_for_post(post_id) do
    from(c in Comment, where: c.post_id == ^post_id, order_by: [asc: c.inserted_at])
    |> Repo.all()
  end

  def create_comment(post_id, attrs) do
    %Comment{}
    |> Comment.changeset(Map.put(attrs, "post_id", post_id))
    |> Repo.insert()
  end

  def change_comment(%Comment{} = comment, attrs \\ %{}) do
    Comment.changeset(comment, attrs)
  end
end