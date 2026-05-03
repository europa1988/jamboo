defmodule Jamboo.Repo.Migrations.CreatePosts do
  use Ecto.Migration

  def change do
    create table(:posts) do
      add :title, :string
      add :body, :text
      add :vote_score, :integer, default: 0
      add :author_nickname, :string
      add :is_microblog, :boolean, default: false
      add :tags, :string

      timestamps(type: :utc_datetime)
    end
  end
end