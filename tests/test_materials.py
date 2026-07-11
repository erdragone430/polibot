from unittest.mock import MagicMock, patch

from polibot.storage.materials import save_material
from polibot.storage.models import Material


def test_save_material_uploads_then_persists_with_metadata():
    fake_session = MagicMock()
    fake_session.__enter__.return_value = fake_session

    with (
        patch("polibot.storage.materials.ensure_tables"),
        patch(
            "polibot.storage.materials.upload_file",
            return_value="http://rustfs/course/topic/x.pdf",
        ) as fake_upload,
        patch("polibot.storage.materials.SessionLocal", return_value=fake_session),
    ):
        material = save_material(
            "/tmp/exercise.pdf", author="prof", course="CS101", topic="recursion"
        )

    fake_upload.assert_called_once()
    called_key = fake_upload.call_args.args[1]
    assert called_key.startswith("CS101/recursion/")
    assert called_key.endswith(".pdf")

    assert isinstance(material, Material)
    assert material.url == "http://rustfs/course/topic/x.pdf"
    assert material.author == "prof"
    assert material.course == "CS101"
    assert material.topic == "recursion"
    fake_session.add.assert_called_once_with(material)
    fake_session.commit.assert_called_once()


if __name__ == "__main__":
    test_save_material_uploads_then_persists_with_metadata()
    print("ok")
