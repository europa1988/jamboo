defmodule JambooWeb.PostHTML do
  @moduledoc "Шаблоны и хелперы для постов"
  use JambooWeb, :html

  embed_templates "post_html/*"

  def render("post_vote.html", assigns) do
    post_vote(assigns)
  end

  @doc """
  Renders the post voting component.
  """
  attr :post, Jamboo.Content.Post, required: true

  def post_vote(assigns) do
    ~H"""
    <div class="flex flex-col items-center space-y-1 vote-container" id={"post-vote-#{@post.id}"}>
      <button
        hx-put={~p"/posts/#{@post.id}/upvote"}
        hx-target="closest .vote-container"
        hx-swap="outerHTML"
        class="p-2 hover:bg-gray-100 rounded-full transition-colors"
        title="Повысить рейтинг"
      >
        <.icon name="hero-arrow-up" class="text-gray-600 hover:text-orange-500 size-6" />
      </button>

      <span class={["font-bold text-lg", @post.vote_score > 0 && "text-orange-500", @post.vote_score <= 0 && "text-gray-700"]}>
        {@post.vote_score}
      </span>

      <button
        hx-put={~p"/posts/#{@post.id}/downvote"}
        hx-target="closest .vote-container"
        hx-swap="outerHTML"
        class="p-2 hover:bg-gray-100 rounded-full transition-colors"
        title="Понизить рейтинг"
      >
        <.icon name="hero-arrow-down" class="text-gray-600 hover:text-blue-500 size-6" />
      </button>
    </div>
    """
  end
end
