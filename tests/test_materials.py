import os
from polibot.storage.materials import save_material
from polibot.storage.models import Material
from polibot.storage.postgres import SessionLocal, ensure_tables
from polibot.storage.rustfs_client import get_rustfs_client
from polibot.config import get_settings

def test_save_material_uploads_then_persists_with_metadata_live():
    # Setup live db
    ensure_tables()

    # Ensure rustfs bucket exists
    settings = get_settings()
    s3_client = get_rustfs_client()
    try:
        s3_client.create_bucket(Bucket=settings.rustfs_bucket)
    except Exception:
        pass

    # Create dummy pdf
    dummy_pdf_path = "/tmp/dummy_test_exercise.pdf"
    with open(dummy_pdf_path, "w") as f:
        f.write("Dummy PDF content")

    material = save_material(
        dummy_pdf_path, author="prof", course="CS101", topic="recursion_live"
    )

    assert isinstance(material, Material)
    assert material.url.startswith(f"{settings.rustfs_endpoint}/{settings.rustfs_bucket}/CS101/recursion_live/")
    assert material.url.endswith(".pdf")
    assert material.author == "prof"
    assert material.course == "CS101"
    assert material.topic == "recursion_live"

    # Verify it was persisted in postgres
    with SessionLocal() as session:
        fetched = session.query(Material).filter_by(id=material.id).first()
        assert fetched is not None
        assert fetched.url == material.url

    os.remove(dummy_pdf_path)

if __name__ == "__main__":
    test_save_material_uploads_then_persists_with_metadata_live()
    print("ok")
