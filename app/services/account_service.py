from datetime import UTC, datetime
import re
from uuid import uuid4

from werkzeug.security import check_password_hash, generate_password_hash

from ..extensions import get_metadata_collection


_EMAIL_PATTERN = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")


def _users():
    return get_metadata_collection("usuarios_v1", "account_records")


def _profile(user_id, metadata):
    return {
        "id": user_id,
        "name": metadata["name"],
        "email": metadata["email_normalized"],
        "role": metadata["role"],
    }


def find_user_by_email(email):
    result = _users().get(
        where={"email_normalized": email},
        include=["metadatas"],
        limit=1,
    )
    if not result["ids"]:
        return None
    return result["ids"][0], result["metadatas"][0]


def find_user_by_id(user_id):
    result = _users().get(ids=[user_id], include=["metadatas"])
    if not result["ids"]:
        return None
    return result["ids"][0], result["metadatas"][0]


def create_user(name, email, password, role="user"):
    name = name.strip()
    email_normalized = email.strip().casefold()
    if not 2 <= len(name) <= 80:
        raise ValueError("El nombre debe tener entre 2 y 80 caracteres.")
    if len(email_normalized) > 254 or not _EMAIL_PATTERN.fullmatch(email_normalized):
        raise ValueError("Escribe un correo electrónico válido.")
    if not 12 <= len(password) <= 1024:
        raise ValueError("La contraseña debe tener entre 12 y 1,024 caracteres.")
    if role not in {"user", "admin"}:
        raise ValueError("El rol solicitado no es válido.")
    users = _users()
    if users.get(where={"email_normalized": email_normalized}, limit=1)["ids"]:
        raise ValueError("Ya existe una cuenta con ese correo.")

    user_id = str(uuid4())
    metadata = {
        "name": name,
        "email_normalized": email_normalized,
        "password_hash": generate_password_hash(password, method="scrypt"),
        "role": role,
        "created_at": datetime.now(UTC).isoformat(),
        "active": True,
    }
    # This collection is for exact ID/metadata lookups, never semantic search.
    # The one-dimensional sentinel avoids downloading Chroma's default embedder.
    users.add(
        ids=[user_id],
        embeddings=[[0.0]],
        documents=["account_record"],
        metadatas=[metadata],
    )
    return _profile(user_id, metadata)


def authenticate(email, password):
    found = find_user_by_email(email.strip().casefold())
    if found is None:
        return None
    user_id, metadata = found
    if not metadata.get("active") or not check_password_hash(
        metadata["password_hash"], password
    ):
        return None
    return _profile(user_id, metadata)


def promote_user_to_admin(email):
    found = find_user_by_email(email.strip().casefold())
    if found is None:
        return False
    user_id, metadata = found
    metadata["role"] = "admin"
    _users().update(ids=[user_id], metadatas=[metadata])
    return True
