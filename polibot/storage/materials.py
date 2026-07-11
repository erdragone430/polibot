import uuid
from pathlib import Path

from polibot.storage.models import Material
from polibot.storage.postgres import SessionLocal, ensure_tables
from polibot.storage.rustfs_client import upload_file


def save_material(pdf_path: str, author: str, course: str, topic: str) -> Material:
    ensure_tables()

    key = f"{course}/{topic}/{uuid.uuid4()}{Path(pdf_path).suffix}"
    url = upload_file(pdf_path, key)

    material = Material(url=url, author=author, course=course, topic=topic)
    with SessionLocal() as session:
        session.add(material)
        session.commit()
        session.refresh(material)

    return material
