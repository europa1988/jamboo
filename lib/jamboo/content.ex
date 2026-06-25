defmodule Jamboo.Content do
  import Ecto.Query, warn: false
  alias Jamboo.Repo
  alias Jamboo.Content.Post

  def list_posts do
    Repo.all(from p in Post, order_by: [desc: p.inserted_at])
  end

  def get_post!(id), do: Repo.get!(Post, id)

  def create_post(attrs) do
    %Post{}
    |> Post.changeset(attrs)
    |> Repo.insert()
  end

  def update_post(%Post{} = post, attrs) do
    post
    |> Post.changeset(attrs)
    |> Repo.update()
  end

  def delete_post(%Post{} = post) do
    Repo.delete(post)
  end

  def change_post(%Post{} = post, attrs \\ %{}) do
    Post.changeset(post, attrs)
  end

  def upvote(id), do: change_vote(id, 1)
  def downvote(id), do: change_vote(id, -1)

  defp change_vote(id, delta) do
    # Преобразуем id в целое число (на случай, если пришла строка)
    int_id = String.to_integer("#{id}")

    {1, _} =
      from(p in Post, where: p.id == ^int_id)
      |> Repo.update_all(inc: [vote_score: delta])

    {:ok, Repo.get!(Post, int_id)}
  end
end
