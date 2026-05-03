   defmodule Jamboo.Repo do
     use Ecto.Repo,
       otp_app: :jamboo,
       adapter: Ecto.Adapters.SQLite3
   end