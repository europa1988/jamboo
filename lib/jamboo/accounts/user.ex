defmodule Jamboo.Accounts.User do
  use Ecto.Schema
  import Ecto.Changeset
  alias Jamboo.Accounts.User

  schema "users" do
    field :email, :string
    field :hashed_password, :string
    field :confirmed_at, :naive_datetime

    # Виртуальное поле для ввода пароля
    field :password, :string, virtual: true

    timestamps()
  end

  @doc """
  Регистрационный changeset: принимает email и password.
  """
  def registration_changeset(user, attrs, _opts \\ []) do
    user
    |> cast(attrs, [:email, :password])
    |> validate_required([:email, :password],
      message: "не может быть пустым"
    )
    |> validate_email()
    |> validate_length(:password,
      min: 6,
      too_short: "слишком короткий пароль (минимум %{count} символов)"
    )
    |> put_password_hash()
  end

  defp validate_email(changeset) do
    changeset
    |> validate_format(:email, ~r/^[^\\s]+@[^\\s]+$/, message: "должен содержать @ и не иметь пробелов")
    |> validate_length(:email, max: 160)
    |> unsafe_validate_unique(:email, Jamboo.Repo)
    |> unique_constraint(:email)
  end

  defp put_password_hash(%Ecto.Changeset{valid?: true, changes: %{password: password}} = changeset) do
    put_change(changeset, :hashed_password, Pbkdf2.hash_pwd_salt(password))
  end

  defp put_password_hash(changeset), do: changeset

  def valid_password?(%User{hashed_password: hashed_password}, password)
      when is_binary(hashed_password) and is_binary(password) do
    Pbkdf2.verify_pass(password, hashed_password)
  end

  def valid_password?(_, _), do: false

  def confirm_changeset(user, attrs \\ %{}) do
    user
    |> cast(attrs, [:confirmed_at])
    |> validate_required([:confirmed_at])
  end
end