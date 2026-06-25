defmodule Jamboo.Content.Post do
  use Ecto.Schema
  import Ecto.Changeset

  schema "posts" do
    field :title, :string
    field :body, :string
    field :vote_score, :integer, default: 0
    field :author_nickname, :string
    field :is_microblog, :boolean, default: false
    field :tags, :string

    timestamps()
  end

  @doc false
  def changeset(post, attrs) do
    post
    |> cast(attrs, [:title, :body, :author_nickname, :is_microblog, :tags])
    |> validate_required([:title, :body, :author_nickname],
      message: "не может быть пустым"
    )
    |> validate_length(:title,
      min: 3,
      max: 200,
      too_short: "слишком короткий (минимум %{count} символов)",
      too_long: "слишком длинный (максимум %{count} символов)"
    )
  end
end
