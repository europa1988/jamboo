defmodule Jamboo.Comments.Comment do
  use Ecto.Schema
  import Ecto.Changeset

  schema "comments" do
    field :body, :string
    field :vote_score, :integer, default: 0
    field :author_nickname, :string
    belongs_to :user, Jamboo.Accounts.User
    belongs_to :post, Jamboo.Content.Post
    belongs_to :parent, Jamboo.Comments.Comment

    timestamps()
  end

  def changeset(comment, attrs) do
    comment
    |> cast(attrs, [:body, :author_nickname])
    |> validate_required([:body, :post_id])
  end
end