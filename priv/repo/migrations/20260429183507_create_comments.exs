defmodule Jamboo.Repo.Migrations.CreateComments do
  use Ecto.Migration

  def change do
    create table(:comments) do
      add :body, :text
      add :vote_score, :integer, default: 0
      add :user_id, references(:users), null: true
      add :post_id, references(:posts), null: false
      add :parent_id, references(:comments, on_delete: :nothing), null: true

      timestamps(type: :utc_datetime)
    end

    create index(:comments, [:user_id])
    create index(:comments, [:post_id])
  end
end
