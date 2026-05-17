"""HTTP-level tests for ``GET /api/parsed-documents/{id}/images/{path}``.

The reader fetches each ``![](images/<sha>.jpg)`` reference through this
endpoint, so we exercise it via FastAPI's ``TestClient`` (no live socket
needed). Three concerns drive the coverage:

  1. **Auth shape.** ``<img src>`` can't attach an ``Authorization``
     header, so the endpoint also accepts ``?token=`` — but ONLY as a
     fallback. A wrong header must still fail even if the right token
     is present in the query, otherwise an attacker could combine a
     leaked header with a valid query token to bypass detection.
  2. **Content delivery.** Bytes round-trip unchanged and the
     ``Content-Type`` is inferred from the file extension (so the
     browser actually renders ``.png`` as an image).
  3. **Path safety.** Traversal-shaped paths are refused at the storage
     layer, which surfaces as ``400`` or ``404`` — never a ``200`` that
     reads a file outside the document directory.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

import revisica.api as api
from revisica.ingestion.storage import save_parsed_document
from revisica.ingestion.types import (
    DocumentMetadata,
    ParsedImage,
    RevisicaDocument,
)


_TINY_PNG = bytes.fromhex(
    "89504e470d0a1a0a0000000d49484452000000010000000108020000"
    "00907753de0000000c49444154789c63f80f00010101001827d50f00"
    "00000049454e44ae426082"
)

_FAKE_TOKEN = "test-token-for-image-endpoint"


@pytest.fixture
def api_client(monkeypatch, tmp_path):
    """A TestClient bound to an isolated parsed-documents root + fake token.

    The api module reads ``_API_TOKEN`` at import time, so we patch the
    module attribute directly rather than fiddling with env vars and
    reloading. ``REVISICA_PARSED_DOCUMENTS_DIR`` is set the same way as
    in the storage tests so each test sees its own clean library.
    """
    monkeypatch.setenv("REVISICA_PARSED_DOCUMENTS_DIR", str(tmp_path))
    monkeypatch.setattr(api, "_API_TOKEN", _FAKE_TOKEN)
    return TestClient(api.app)


@pytest.fixture
def seeded_parsed_document(api_client) -> str:
    """Save one parsed document with a single image and return its id."""
    doc = RevisicaDocument(
        source_path="/seed/paper.pdf",
        parser_used="mineru",
        markdown="![](images/figure.png)",
        metadata=DocumentMetadata(title="seed"),
    )
    manifest = save_parsed_document(
        doc,
        elapsed_ms=1,
        images=[ParsedImage(relative_path="images/figure.png", data=_TINY_PNG)],
    )
    return manifest["id"]


def _image_url(parsed_id: str, path: str = "figure.png") -> str:
    return f"/api/parsed-documents/{parsed_id}/images/{path}"


class TestImageEndpointAuth:
    """Header auth, query auth, and the precedence between them."""

    def test_rejects_request_with_no_token(self, api_client, seeded_parsed_document):
        response = api_client.get(_image_url(seeded_parsed_document))
        assert response.status_code == 401
        # Error message names both supported auth shapes, so a confused
        # caller sees an actionable hint.
        assert "header" in response.json()["detail"].lower()
        assert "token" in response.json()["detail"].lower()

    def test_accepts_correct_header_token(
        self, api_client, seeded_parsed_document,
    ):
        response = api_client.get(
            _image_url(seeded_parsed_document),
            headers={"Authorization": f"Bearer {_FAKE_TOKEN}"},
        )
        assert response.status_code == 200
        assert response.content == _TINY_PNG

    def test_accepts_correct_query_token(
        self, api_client, seeded_parsed_document,
    ):
        response = api_client.get(
            f"{_image_url(seeded_parsed_document)}?token={_FAKE_TOKEN}",
        )
        assert response.status_code == 200
        assert response.content == _TINY_PNG

    def test_rejects_wrong_header_token(
        self, api_client, seeded_parsed_document,
    ):
        response = api_client.get(
            _image_url(seeded_parsed_document),
            headers={"Authorization": "Bearer wrong-value"},
        )
        assert response.status_code == 401

    def test_rejects_wrong_query_token(
        self, api_client, seeded_parsed_document,
    ):
        response = api_client.get(
            f"{_image_url(seeded_parsed_document)}?token=wrong-value",
        )
        assert response.status_code == 401

    def test_wrong_header_is_not_rescued_by_correct_query_token(
        self, api_client, seeded_parsed_document,
    ):
        """If a header is present, it MUST be valid — no query fallback.

        This is the defense-in-depth case: an attacker who somehow
        forces a request with a stale/bad header should not be able to
        slip past auth just by also appending a correct ``?token=``.
        """
        response = api_client.get(
            f"{_image_url(seeded_parsed_document)}?token={_FAKE_TOKEN}",
            headers={"Authorization": "Bearer wrong-value"},
        )
        assert response.status_code == 401

    def test_malformed_authorization_header_rejected(
        self, api_client, seeded_parsed_document,
    ):
        """Anything that isn't ``Bearer <token>`` must fail auth."""
        response = api_client.get(
            _image_url(seeded_parsed_document),
            headers={"Authorization": "Basic dXNlcjpwYXNz"},
        )
        assert response.status_code == 401


class TestImageEndpointContent:
    """The endpoint actually delivers the right bytes with the right type."""

    def test_round_trips_image_bytes(self, api_client, seeded_parsed_document):
        response = api_client.get(
            f"{_image_url(seeded_parsed_document)}?token={_FAKE_TOKEN}",
        )
        assert response.status_code == 200
        assert response.content == _TINY_PNG

    def test_content_type_is_inferred_from_extension(
        self, api_client, seeded_parsed_document,
    ):
        response = api_client.get(
            f"{_image_url(seeded_parsed_document)}?token={_FAKE_TOKEN}",
        )
        assert response.headers["content-type"] == "image/png"

    def test_serves_jpeg_with_jpeg_content_type(self, api_client):
        # Same parsed-document fixture pattern but seed a JPEG, since
        # ``.jpg`` and ``.png`` go down different mime branches in
        # ``FileResponse``.
        doc = RevisicaDocument(
            source_path="/seed/paper.pdf",
            parser_used="mineru",
            markdown="![](images/fig.jpg)",
        )
        manifest = save_parsed_document(
            doc,
            elapsed_ms=1,
            images=[ParsedImage(relative_path="images/fig.jpg", data=b"JPEGBYTES")],
        )
        response = api_client.get(
            _image_url(manifest["id"], "fig.jpg") + f"?token={_FAKE_TOKEN}",
        )
        assert response.status_code == 200
        assert response.headers["content-type"] == "image/jpeg"


class TestImageEndpointErrors:
    """Lookups that don't resolve cleanly return clear status codes."""

    def test_missing_image_returns_404(self, api_client, seeded_parsed_document):
        response = api_client.get(
            _image_url(seeded_parsed_document, "no-such-image.png")
            + f"?token={_FAKE_TOKEN}",
        )
        assert response.status_code == 404

    def test_missing_parsed_document_returns_404(self, api_client):
        # ``no.such.id`` matches the safe-id regex but no directory
        # exists with that name, so the lookup succeeds at the safety
        # layer and fails at the file-existence check.
        response = api_client.get(
            "/api/parsed-documents/no.such.id/images/anything.png"
            f"?token={_FAKE_TOKEN}",
        )
        assert response.status_code == 404

    def test_invalid_document_id_returns_400(self, api_client):
        # ``@`` is outside the SAFE_ID character class but doesn't break
        # path routing, so Starlette delivers it to the endpoint, which
        # surfaces the regex's ``ValueError`` as a clean 400. (A literal
        # ``/`` would re-route, which is why we don't use one here.)
        response = api_client.get(
            "/api/parsed-documents/has@slash/images/anything.png"
            f"?token={_FAKE_TOKEN}",
        )
        assert response.status_code == 400

    def test_traversal_does_not_leak_files(
        self, api_client, seeded_parsed_document, tmp_path,
    ):
        # Plant a file outside the parsed-documents root, then try to
        # reach it via ``..`` segments in the image path. The endpoint
        # must respond with 4xx and the body must not contain the file.
        secret = tmp_path / "secret.txt"
        secret.write_text("this should never be readable via the API")
        response = api_client.get(
            _image_url(seeded_parsed_document, "../../../secret.txt")
            + f"?token={_FAKE_TOKEN}",
        )
        assert response.status_code in (400, 404)
        assert b"this should never be readable" not in response.content
