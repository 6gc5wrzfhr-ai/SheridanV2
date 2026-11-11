"""Regression tests for Sheridan's local image provider and reference library."""

from pathlib import Path

import pytest

from herandhim.core.image_gen import selfie
from herandhim.core.image_gen.photo_album import PhotoAlbum


def test_local_comfyui_provider_enables_selfies(monkeypatch):
    monkeypatch.setattr(selfie.config, "get_bool", lambda *a, **k: True)
    monkeypatch.setattr(
        "herandhim.core.image_gen.generator._provider", lambda: "comfyui"
    )
    assert selfie.is_enabled() is True


def test_keyless_pollinations_provider_enables_selfies(monkeypatch):
    monkeypatch.setattr(selfie.config, "get_bool", lambda *a, **k: True)
    monkeypatch.setattr(
        "herandhim.core.image_gen.generator._provider", lambda: "pollinations"
    )
    assert selfie.is_enabled() is True


def test_cloud_provider_without_key_is_disabled(monkeypatch):
    monkeypatch.setattr(selfie.config, "get_bool", lambda *a, **k: True)

    def missing_key(provider):
        raise selfie.SeedreamError("missing key")

    monkeypatch.setattr(
        "herandhim.core.image_gen.generator._provider", lambda: "seedream"
    )
    monkeypatch.setattr(
        "herandhim.core.image_gen.generator._read_api_key", missing_key
    )
    assert selfie.is_enabled() is False


def test_disabled_feature_stays_disabled(monkeypatch):
    monkeypatch.setattr(selfie.config, "get_bool", lambda *a, **k: False)
    assert selfie.is_enabled() is False


def test_external_reference_directory_is_read_only_and_master_is_selected(
    tmp_path, monkeypatch
):
    source = tmp_path / "Image References"
    source.mkdir()
    body = source / "01_body.png"
    master = source / "Sheridan_Master.png"
    tattoo = source / "02_tattoos.png"
    for path in (body, master, tattoo):
        path.write_bytes(b"image")

    monkeypatch.setenv("HERANDHIM_IMAGE_REFERENCE_DIR", str(source))
    album = PhotoAlbum(root=str(tmp_path / "album"))

    assert set(album.list_references()) == {
        str(body.resolve()), str(master.resolve()), str(tattoo.resolve())
    }
    assert album.primary_reference() == str(master.resolve())
    assert master.exists() and body.exists() and tattoo.exists()


def test_explicit_primary_reference_takes_precedence(tmp_path, monkeypatch):
    source = tmp_path / "refs"
    source.mkdir()
    master = source / "master.png"
    alternate = source / "Sheridan_Master.png"
    master.write_bytes(b"master")
    alternate.write_bytes(b"alternate")

    monkeypatch.setenv("HERANDHIM_IMAGE_REFERENCE_DIR", str(source))
    monkeypatch.setenv("HERANDHIM_IMAGE_PRIMARY_REFERENCE", str(master))
    album = PhotoAlbum(root=str(tmp_path / "album"))

    assert album.primary_reference() == str(master.resolve())


def test_promoting_reference_preserves_other_images_and_extension(tmp_path, monkeypatch):
    source = tmp_path / "Image References"
    source.mkdir()
    face = source / "Sheridan_Master.png"
    body = source / "body.png"
    face.write_bytes(b"face")
    body.write_bytes(b"body")
    monkeypatch.setenv("HERANDHIM_IMAGE_REFERENCE_DIR", str(source))

    album = PhotoAlbum(root=str(tmp_path / "album"))
    promoted = album.set_reference(str(face))

    assert Path(promoted).name == "companion_reference.png"
    assert Path(promoted).read_bytes() == b"face"
    assert face.exists()
    assert body.exists()
    assert str(body.resolve()) in album.list_references()


def test_album_instances_use_their_own_reference_directory(tmp_path, monkeypatch):
    monkeypatch.delenv("HERANDHIM_IMAGE_REFERENCE_DIR", raising=False)
    first = PhotoAlbum(root=str(tmp_path / "first"))
    second = PhotoAlbum(root=str(tmp_path / "second"))
    image = tmp_path / "face.jpg"
    image.write_bytes(b"face")

    first.set_reference(str(image))

    assert first.primary_reference() is not None
    assert second.primary_reference() is None
