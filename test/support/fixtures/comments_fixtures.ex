defmodule Jamboo.CommentsFixtures do
  @moduledoc """
  This module defines test helpers for creating
  entities via the `Jamboo.Comments` context.
  """

  @doc """
  Generate a comment.
  """
  def comment_fixture(attrs \\ %{}) do
    {:ok, comment} =
      attrs
      |> Enum.into(%{

      })
      |> Jamboo.Comments.create_comment()

    comment
  end
end
