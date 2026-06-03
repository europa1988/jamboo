defmodule Jamboo.Repo.Migrations.UpdateCommentsAndPosts do
  use Ecto.Migration

  def change do
    rename table(:posts), :is_microblog, to: :microblog

    alter table(:comments) do
      add :author_nickname, :string
    end
  end
end
