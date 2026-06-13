defmodule JambooWeb.PostHTML do
  @moduledoc "Шаблоны и хелперы для постов"
  use JambooWeb, :html

  embed_templates "post_html/*"

  @doc """
  Возвращает HTML‑фрагмент блока голосования для поста.
  """
  attr :post, :any, required: true

  def post_vote(assigns) do
    ~H"""
    <div class="flex flex-col items-center space-y-1 vote-container">
      <button
        hx-put={~p"/posts/#{@post.id}/upvote"}
        hx-target="closest .vote-container"
        hx-swap="outerHTML"
        class="p-2 hover:bg-gray-100 rounded-full transition-colors"
        title="Повысить рейтинг"
      >
        <.icon name="hero-arrow-up" class="size-6 text-gray-600 hover:text-orange-500" />
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
        <.icon name="hero-arrow-down" class="size-6 text-gray-600 hover:text-blue-500" />
      </button>
    </div>
    """
  end
end