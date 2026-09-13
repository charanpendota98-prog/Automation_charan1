"""v31 Student Internet Center landing page + private case metadata tests."""
import hashlib
import sqlite3
import sys
import tempfile
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from autoblog import config, service_center  # noqa: E402


def test_service_page_is_transparent_and_configured():
    values = {
        "SERVICE_CENTER_NAME": "StudentUp Internet Center",
        "SERVICE_CENTER_CITY": "Hyderabad",
        "SERVICE_CENTER_PHONE": "+919876543210",
        "SERVICE_CENTER_WHATSAPP": "+919876543210",
        "SERVICE_CENTER_UPLOAD_URL": "https://upload.example.test/one-time",
    }
    with mock.patch.multiple(config, **values):
        out = service_center.build_page_html()
    assert "StudentUp Internet Center" in out
    assert service_center.SERVICE_PAGE_MARKER in out
    assert "tel:+919876543210" in out
    assert "https://wa.me/919876543210" in out
    assert "upload.example.test" in out
    assert "OTP" in out and "UPI PIN" in out and "passwords" in out
    assert "selection guarantee" in out
    assert "hidden charges" in out


def test_missing_phone_does_not_create_fake_contact():
    with mock.patch.object(config, "SERVICE_CENTER_PHONE", ""), \
         mock.patch.object(config, "SERVICE_CENTER_WHATSAPP", ""), \
         mock.patch.object(config, "SERVICE_CENTER_UPLOAD_URL", ""):
        out = service_center.build_page_html()
    assert "tel:" not in out and "wa.me" not in out
    assert "secure upload link" in out.lower()


def test_service_page_preserves_manual_wordpress_copy():
    class FakeWP:
        def get_page_for_edit(self, slug):
            return {"id": 7, "link": "https://example.test/student-services/",
                    "content": "<p>Manual copy written in WordPress.</p>"}

        def upsert_page(self, *args, **kwargs):
            raise AssertionError("manual page must not be overwritten")

    with mock.patch.object(config, "SERVICE_CENTER_PAGE_SLUG", "student-services"):
        result = service_center.publish_page(FakeWP(), dry=False)
    assert result["status"] == "manual-preserved"
    assert "manual" in result["detail"]


def test_case_metadata_and_retention():
    db = Path(tempfile.mkdtemp()) / "cases.db"
    try:
        try:
            service_center.create_case("A Student", "+919876543210", "jobs", False, path=db)
            raise AssertionError("consent must be required")
        except ValueError as exc:
            assert "consent" in str(exc)
        case_id = service_center.create_case(
            "A Student", "+919876543210", "jobs", True,
            notes="Client asked for eligibility review", path=db)
        assert case_id.startswith("SU-")
        digest = hashlib.sha256(b"private-document").hexdigest()
        doc_id = service_center.add_document(
            case_id, "../aadhaar.pdf", "https://private.example.test/object/1",
            digest, path=db)
        assert doc_id > 0
        service_center.update_status(case_id, "reviewing", actor="staff", path=db)
        service_center.update_status(case_id, "completed", actor="staff", note="receipt sent", path=db)
        case = service_center.get_case(case_id, path=db)
        assert case["status"] == "completed"
        assert case["documents"][0]["file_name"] == "aadhaar.pdf"
        assert case["events"][-1]["status"] == "completed"
        try:
            service_center.update_status(case_id, "new", path=db)
            raise AssertionError("terminal case reopened")
        except ValueError as exc:
            assert "terminal" in str(exc)
        with sqlite3.connect(db) as conn:
            conn.execute("UPDATE cases SET updated_at='2020-01-01T00:00:00+00:00' WHERE case_id=?", (case_id,))
        assert service_center.purge_expired(db, retention_days=1) == 1
        assert service_center.get_case(case_id, path=db) is None
    finally:
        db.unlink(missing_ok=True)


def main():
    test_service_page_is_transparent_and_configured()
    print("  service page CTA/safety copy ✔")
    test_missing_phone_does_not_create_fake_contact()
    print("  missing contact config is honest ✔")
    test_service_page_preserves_manual_wordpress_copy()
    print("  manual WordPress service-page copy is preserved ✔")
    test_case_metadata_and_retention()
    print("  consented case metadata + document reference + purge ✔")
    print("ALL v31 TESTS PASSED ✔")


if __name__ == "__main__":
    main()
