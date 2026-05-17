"""Tests for image asset persistence inside the parsed-document store.

The reader renders ``![](images/<sha>.jpg)`` references against this
on-disk layout, so we lock in three contracts here:

  1. ``save_parsed_document(images=...)`` writes each ParsedImage to
     ``<doc_dir>/<relative_path>`` byte-for-byte.
  2. Path-traversal-shaped relative paths are silently dropped (defense
     in depth — parsers should never produce them, but a compromised
     upstream must not be able to clobber files outside the doc dir).
  3. ``parsed_document_image_path`` refuses lookups that escape the doc
     dir, and otherwise returns an on-disk path the caller can stat.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from revisica.ingestion.storage import (
    parsed_document_image_path,
    parsed_documents_root,
    save_parsed_document,
)
from revisica.ingestion.types import (
    DocumentMetadata,
    ParsedImage,
    RevisicaDocument,
)


@pytest.fixture
def isolated_parsed_documents_root(tmp_path, monkeypatch):
    """Pin the parsed-documents root to a tmp dir for the test's lifetime.

    Reads ``REVISICA_PARSED_DOCUMENTS_DIR`` on each call to
    ``parsed_documents_root``, so a monkeypatched env var fully isolates
    one test from another's on-disk state.
    """
    monkeypatch.setenv("REVISICA_PARSED_DOCUMENTS_DIR", str(tmp_path))
    return tmp_path


def _make_document(markdown: str = "# t") -> RevisicaDocument:
    return RevisicaDocument(
        source_path="/some/paper.pdf",
        parser_used="mineru",
        markdown=markdown,
        metadata=DocumentMetadata(title="t"),
    )


# 1x1 PNG, used as a stand-in for "real" image bytes throughout these
# tests — small enough to inline, valid enough that any image library
# could decode it if we ever wanted to extend a test to do so.
_TINY_PNG = bytes.fromhex(
    "89504e470d0a1a0a0000000d49484452000000010000000108020000"
    "00907753de0000000c49444154789c63f80f00010101001827d50f00"
    "00000049454e44ae426082"
)


class TestSaveParsedDocumentWithImages:
    """``save_parsed_document(images=...)`` writes each image to disk."""

    def test_writes_images_under_doc_dir(self, isolated_parsed_documents_root):
        doc = _make_document(markdown="![](images/a.png)")
        images = [ParsedImage(relative_path="images/a.png", data=_TINY_PNG)]

        manifest = save_parsed_document(doc, elapsed_ms=10, images=images)

        on_disk = (
            parsed_documents_root() / manifest["id"] / "images" / "a.png"
        )
        assert on_disk.is_file()
        assert on_disk.read_bytes() == _TINY_PNG

    def test_no_images_arg_skips_images_dir(self, isolated_parsed_documents_root):
        """A call without ``images=`` must not create an empty ``images/``.

        This is what every call site looked like before this feature
        landed, and we don't want to suddenly start producing empty
        directories that confuse a casual ``ls`` of the library.
        """
        doc = _make_document()
        manifest = save_parsed_document(doc, elapsed_ms=10)
        doc_dir = parsed_documents_root() / manifest["id"]
        assert doc_dir.is_dir()
        assert not (doc_dir / "images").exists()

    def test_empty_images_iterable_skips_images_dir(
        self, isolated_parsed_documents_root,
    ):
        """An empty iterable behaves the same as omitting ``images``."""
        doc = _make_document()
        manifest = save_parsed_document(doc, elapsed_ms=10, images=[])
        doc_dir = parsed_documents_root() / manifest["id"]
        assert not (doc_dir / "images").exists()

    def test_writes_multiple_images(self, isolated_parsed_documents_root):
        doc = _make_document()
        images = [
            ParsedImage(relative_path="images/a.png", data=b"AAA"),
            ParsedImage(relative_path="images/b.png", data=b"BBBB"),
        ]
        manifest = save_parsed_document(doc, elapsed_ms=10, images=images)
        doc_dir = parsed_documents_root() / manifest["id"]
        assert (doc_dir / "images" / "a.png").read_bytes() == b"AAA"
        assert (doc_dir / "images" / "b.png").read_bytes() == b"BBBB"

    def test_creates_nested_image_subdirs(self, isolated_parsed_documents_root):
        """Nested relative paths get intermediate dirs created.

        Mineru today only emits ``images/<sha>.jpg`` (flat), but the
        storage layer doesn't constrain depth — we test the nested case
        so a future parser that organizes by page or by figure doesn't
        silently fail on ``mkdir``.
        """
        doc = _make_document()
        images = [
            ParsedImage(relative_path="images/figs/fig1.png", data=b"DEEP"),
        ]
        manifest = save_parsed_document(doc, elapsed_ms=10, images=images)
        nested = (
            parsed_documents_root() / manifest["id"]
            / "images" / "figs" / "fig1.png"
        )
        assert nested.read_bytes() == b"DEEP"


class TestSaveParsedDocumentRejectsTraversal:
    """Malicious relative_paths must be silently dropped, not written.

    "Silently" because a partial save would still be a valid document
    save — we just refuse to clobber files outside the doc dir.
    """

    def test_traversal_with_dotdot_skipped(self, isolated_parsed_documents_root):
        doc = _make_document()
        images = [
            ParsedImage(relative_path="../escape.png", data=b"NO"),
            ParsedImage(relative_path="images/ok.png", data=b"OK"),
        ]
        manifest = save_parsed_document(doc, elapsed_ms=10, images=images)
        doc_dir = parsed_documents_root() / manifest["id"]
        # The legitimate image still landed.
        assert (doc_dir / "images" / "ok.png").read_bytes() == b"OK"
        # The escape attempt did NOT write a sibling next to the doc dir.
        sibling = parsed_documents_root() / "escape.png"
        assert not sibling.exists()

    def test_absolute_path_skipped(self, isolated_parsed_documents_root, tmp_path):
        doc = _make_document()
        forbidden = tmp_path / "absolute-target.png"
        images = [
            ParsedImage(relative_path=str(forbidden), data=b"NO"),
        ]
        save_parsed_document(doc, elapsed_ms=10, images=images)
        assert not forbidden.exists()

    def test_empty_relative_path_skipped(self, isolated_parsed_documents_root):
        doc = _make_document()
        # Trying to write "" would otherwise resolve to the doc dir
        # itself, which is a directory, which would raise an unhelpful
        # error deep inside Path.write_bytes. Make sure we drop it
        # before that happens.
        images = [ParsedImage(relative_path="", data=b"NO")]
        save_parsed_document(doc, elapsed_ms=10, images=images)
        # No crash, doc still saved fine.


class TestParsedDocumentImagePath:
    """``parsed_document_image_path`` is the storage-layer lookup helper."""

    def _seed(self, isolated_root: Path) -> str:
        doc = _make_document()
        images = [ParsedImage(relative_path="images/a.png", data=_TINY_PNG)]
        manifest = save_parsed_document(doc, elapsed_ms=10, images=images)
        return manifest["id"]

    def test_returns_path_for_existing_image(
        self, isolated_parsed_documents_root,
    ):
        parsed_id = self._seed(isolated_parsed_documents_root)
        path = parsed_document_image_path(parsed_id, "images/a.png")
        assert path.is_file()
        assert path.read_bytes() == _TINY_PNG

    def test_returns_path_even_when_file_missing(
        self, isolated_parsed_documents_root,
    ):
        """Existence is the caller's responsibility — see api.py.

        The function returns a path inside the doc dir without stat'ing
        first, so callers (the FastAPI endpoint) can decide whether a
        404 or some other response is appropriate.
        """
        parsed_id = self._seed(isolated_parsed_documents_root)
        path = parsed_document_image_path(parsed_id, "images/never-existed.png")
        assert not path.exists()
        # But the returned path is still inside the doc dir.
        assert isolated_parsed_documents_root.resolve() in path.resolve().parents

    def test_rejects_dotdot_traversal(self, isolated_parsed_documents_root):
        parsed_id = self._seed(isolated_parsed_documents_root)
        with pytest.raises(ValueError, match="Invalid image path"):
            parsed_document_image_path(parsed_id, "images/../../../etc/passwd")

    def test_rejects_absolute_path(self, isolated_parsed_documents_root):
        parsed_id = self._seed(isolated_parsed_documents_root)
        # Leading slash gets stripped (matches markdown-style relatives),
        # but the stripped form must still resolve inside the doc dir —
        # ``/etc/passwd`` → ``etc/passwd``, which doesn't exist but is
        # safely inside, so we return a (non-existent) path rather than
        # raise. That's by design and documented in the function.
        path = parsed_document_image_path(parsed_id, "/etc/passwd")
        assert not path.exists()
        assert isolated_parsed_documents_root.resolve() in path.resolve().parents

    def test_rejects_empty_path(self, isolated_parsed_documents_root):
        parsed_id = self._seed(isolated_parsed_documents_root)
        with pytest.raises(ValueError, match="Invalid image path"):
            parsed_document_image_path(parsed_id, "")

    def test_rejects_invalid_document_id(self, isolated_parsed_documents_root):
        # Driven by ``_ensure_safe_id`` in storage.py — any character
        # outside ``[A-Za-z0-9._-]`` rejects the lookup before we even
        # touch the relative path. We expect a different error string
        # than the image-path validators because the failure mode is
        # different.
        with pytest.raises(ValueError, match="Invalid parsed document id"):
            parsed_document_image_path("../escape", "images/a.png")
