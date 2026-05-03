defmodule Jamboo.ContentFixtures do
  @moduledoc """
  This module defines test helpers for creating
  entities via the `Jamboo.Content` context.
  """

  @doc """
  Generate a post.
  """
  def post_fixture(attrs \\ %{}) do
    {:ok, post} =
      attrs
      |> Enum.into(%{

      })
      |> Jamboo.Content.create_post()

    post
  end
end
