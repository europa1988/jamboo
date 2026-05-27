defmodule Jamboo.Repo.Migrations.RenameIsMicroblogToMicroblog do
  use Ecto.Migration

  def change do
    rename table(:posts), :is_microblog, to: :microblog
  end
end
