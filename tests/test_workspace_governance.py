import pytest

from app.workspace.governance import GovernanceError, GovernanceStore


def test_audit_chain_and_revision_history(tmp_path):
    store = GovernanceStore(tmp_path / "governance.sqlite3")
    revision = store.save_revision(
        "document", "42", {"title": "Projeto A", "status": "draft"},
        actor="ana", comment="Versão inicial",
    )
    assert revision == 1
    store.save_revision(
        "document", "42", {"title": "Projeto A", "status": "review"},
        actor="ana", comment="Enviado para revisão",
    )
    revisions = store.list_revisions("document", "42")
    assert [item["revision"] for item in revisions] == [2, 1]
    assert store.verify_audit_chain() is True


def test_approval_requires_existing_revision_and_is_single_decision(tmp_path):
    store = GovernanceStore(tmp_path / "governance.sqlite3")
    with pytest.raises(GovernanceError):
        store.request_approval("document", "7", 1, requested_by="editor")
    revision = store.save_revision("document", "7", {"value": 10}, actor="editor")
    approval_id = store.request_approval("document", "7", revision, requested_by="editor")
    store.review_approval(approval_id, "approved", reviewer="manager", comment="Conferido")
    assert store.list_approvals()[0]["status"] == "approved"
    with pytest.raises(GovernanceError):
        store.review_approval(approval_id, "rejected", reviewer="manager")


def test_role_permissions_are_explicit_and_default_is_read_only(tmp_path):
    store = GovernanceStore(tmp_path / "governance.sqlite3")
    assert store.has_permission("unknown", "workspace.read")
    assert not store.has_permission("unknown", "workspace.edit")
    store.set_role("ana", "editor", changed_by="admin")
    assert store.has_permission("ana", "workspace.edit")
    assert not store.has_permission("ana", "documents.approve")
    with pytest.raises(GovernanceError):
        store.require_permission("ana", "documents.approve")


def test_audit_events_are_hash_chained(tmp_path):
    store = GovernanceStore(tmp_path / "governance.sqlite3")
    store.record_event("ana", "record.updated", "record", 1, {"field": "width"})
    store.record_event("ana", "record.updated", "record", 2, {"field": "span"})
    assert store.verify_audit_chain()
