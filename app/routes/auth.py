import re
import secrets

import click
from flask import Blueprint, current_app, flash, redirect, render_template, request, session, url_for

from ..extensions import limiter
from ..security import require_csrf
from ..services.account_service import authenticate, create_user, promote_user_to_admin


auth_bp = Blueprint("auth", __name__, url_prefix="/auth")
EMAIL_RE = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")


def _start_session(user):
    session.clear()
    session["user_id"] = user["id"]
    session["name"] = user["name"]
    session["role"] = user["role"]
    session["_csrf_token"] = secrets.token_urlsafe(32)


@auth_bp.route("/registro", methods=["GET", "POST"])
@limiter.limit("8 per minute")
def register():
    if request.method == "GET":
        return render_template("auth/register.html")

    require_csrf()
    name = request.form.get("name", "").strip()
    email = request.form.get("email", "").strip().casefold()
    password = request.form.get("password", "")
    confirmation = request.form.get("password_confirmation", "")

    errors = []
    if not 2 <= len(name) <= 80:
        errors.append("Escribe un nombre de entre 2 y 80 caracteres.")
    if len(email) > 254 or not EMAIL_RE.fullmatch(email):
        errors.append("Escribe un correo válido.")
    if not 12 <= len(password) <= 1024:
        errors.append("La contraseña debe tener entre 12 y 1,024 caracteres.")
    if password != confirmation:
        errors.append("Las contraseñas no coinciden.")
    if errors:
        return render_template("auth/register.html", errors=errors, name=name, email=email), 422

    try:
        user = create_user(name, email, password)
    except ValueError as exc:
        return render_template(
            "auth/register.html", errors=[str(exc)], name=name, email=email
        ), 409

    _start_session(user)
    flash("Tu cuenta quedó creada. Ya puedes guardar lugares favoritos.", "success")
    return redirect(url_for("web.index"))


@auth_bp.route("/login", methods=["GET", "POST"])
@limiter.limit("8 per minute")
def login():
    if request.method == "GET":
        return render_template("auth/login.html")

    require_csrf()
    email = request.form.get("email", "").strip().casefold()
    password = request.form.get("password", "")
    user = (
        authenticate(email, password)
        if email and len(email) <= 254 and password and len(password) <= 1024
        else None
    )
    if user is None:
        return render_template(
            "auth/login.html", error="Correo o contraseña incorrectos.", email=email
        ), 401

    _start_session(user)
    flash(f"¡Qué gusto verte, {user['name']}!", "success")
    return redirect(url_for("web.index"))


@auth_bp.post("/logout")
def logout():
    require_csrf()
    session.clear()
    flash("Cerraste sesión.", "info")
    return redirect(url_for("web.index"))


def register_admin_cli(app):
    @app.cli.command("crear-admin")
    def create_admin_command():
        """Create an admin or promote an existing registered account."""
        from ..services.account_service import create_user, find_user_by_email

        email = click.prompt("Correo administrador").strip().casefold()
        existing = find_user_by_email(email)
        if existing:
            promote_user_to_admin(email)
            click.echo("La cuenta existente ahora tiene rol administrador.")
            return

        name = click.prompt("Nombre")
        password = click.prompt(
            "Contraseña (mínimo 12 caracteres)", hide_input=True, confirmation_prompt=True
        )
        if len(password) < 12:
            raise click.ClickException("La contraseña debe tener al menos 12 caracteres.")
        try:
            create_user(name, email, password, role="admin")
        except ValueError as exc:
            raise click.ClickException(str(exc)) from exc
        click.echo("Cuenta administradora creada.")

    @app.cli.command("generar-embeddings")
    def generate_embeddings_command():
        """Index catalogue records saved while the local embedding model was offline."""
        from ..services.place_service import generate_missing_embeddings

        indexed, total = generate_missing_embeddings()
        click.echo(f"Embeddings generados: {indexed} de {total} fichas pendientes.")
