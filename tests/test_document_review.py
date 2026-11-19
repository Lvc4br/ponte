import pytest

from app.documents.review import ExtractionReviewStore, ReviewError


def test_extraction_requires_human_review_and_keeps_source(tmp_path):
    store = ExtractionReviewStore(tmp_path / "review.sqlite3")
    item_id = store.submit(
        document_sha256="abc123", document_path="memorial.pdf",
        source_locator="page:4:table:1:row:2", field_name="vao_m",
        extracted_value=12.5, confidence=0.91,
    )
    item = store.get_item(item_id)
    assert item["status"] == "pending"
    assert item["extracted_value"] == 12.5
    assert item["source_locator"] == "page:4:table:1:row:2"
    assert store.list_items("pending")[0]["id"] == item_id


def test_review_can_approve_reject_or_correct_once(tmp_path):
    store = ExtractionReviewStore(tmp_path / "review.sqlite3")
    item_id = store.submit(
        document_sha256="abc123", document_path="memorial.pdf",
        source_locator="page:2", field_name="width_m", extracted_value=8.0,
    )
    store.review(item_id, "corrected", reviewer="engineer", corrected_value=8.25,
                 comment="Conferido no desenho.")
    item = store.get_item(item_id)
    assert item["status"] == "corrected"
    assert item["reviewed_value"] == 8.25
    with pytest.raises(ReviewError):
        store.review(item_id, "approved", reviewer="engineer")


def test_review_rejects_invalid_confidence_and_missing_reviewer(tmp_path):
    store = ExtractionReviewStore(tmp_path / "review.sqlite3")
    with pytest.raises(ReviewError):
        store.submit(
            document_sha256="abc", document_path="x.pdf", source_locator="p1",
            field_name="length", extracted_value=4, confidence=1.5,
        )
    item_id = store.submit(
        document_sha256="abc", document_path="x.pdf", source_locator="p1",
        field_name="length", extracted_value=4,
    )
    with pytest.raises(ReviewError):
        store.review(item_id, "approved", reviewer=" ")
