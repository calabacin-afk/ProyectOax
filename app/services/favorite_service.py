from datetime import UTC, datetime

from ..extensions import get_metadata_collection


def _favorites():
    return get_metadata_collection("favoritos_v1", "favorite_records")


def favorite_place_ids(user_id):
    result = _favorites().get(
        where={"user_id": user_id},
        include=["metadatas"],
    )
    return {metadata["place_id"] for metadata in result["metadatas"] or []}


def toggle_favorite(user_id, place_id):
    favorites = _favorites()
    record_id = f"{user_id}:{place_id}"
    existing = favorites.get(ids=[record_id], include=[])
    if existing["ids"]:
        favorites.delete(ids=[record_id])
        return False

    favorites.add(
        ids=[record_id],
        embeddings=[[0.0]],
        documents=["favorite_record"],
        metadatas=[
            {
                "user_id": user_id,
                "place_id": place_id,
                "created_at": datetime.now(UTC).isoformat(),
            }
        ],
    )
    return True
