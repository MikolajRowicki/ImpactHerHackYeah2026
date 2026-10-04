"""Rules for the operations added after v0 (the frozen ones are in test_contract_baseline.py)."""

import json

from . import contract as c
from .tools.baseline import V0_OPERATIONS

NEW_OPERATIONS = {
    "delete_account",
    "get_preferences",
    "update_preferences",
    "leave_group",
    "list_invitations",
    "revoke_invitation",
    "list_memberships",
    "signup",
    "activate_account",
    "resend_activation",
    "request_password_reset",
    "confirm_password_reset",
    "change_password",
    "get_summary_extended",
    "get_help",
    "list_task_suggestions",
    "release_task",
    "list_reminders",
    "ai_say_it_for_me",
    "ai_conversation_guide",
}
# Schemas that carry a single answer or a check-in value. Tasks may show a person: they are public.
PRIVATE = {"CheckIn", "CheckInList", "AnswerValue", "ObservationRequest"}


def reachable_from(operation_id):
    op = c.operation_by_id()[operation_id][2]
    names = set()
    for status in op["responses"]:
        names |= c.reachable_schema_names(c.response_schema(op, status))
    return names


def test_the_new_operations_are_exactly_the_planned_twenty():
    ids = set(c.operation_by_id())
    assert ids - set(V0_OPERATIONS) == NEW_OPERATIONS
    assert len(ids) == 23 + 20


def test_no_new_operation_returns_a_check_in_or_an_answer():
    for operation_id in NEW_OPERATIONS:
        assert not reachable_from(operation_id) & PRIVATE, operation_id


def test_the_extended_summary_is_the_summary_plus_reasons_and_help():
    ops = c.operation_by_id()
    summary = c.resolve(c.response_schema(ops["get_summary"][2], "200"))
    extended = c.resolve(c.response_schema(ops["get_summary_extended"][2], "200"))
    assert set(extended["properties"]) == set(summary["properties"]) | {"reasons", "help"}
    forbidden = {
        "answer",
        "answers",
        "question_id",
        "author",
        "created_by",
        "user_id",
        "display_name",
    }
    for node in c.walk(extended):
        assert not forbidden & set(node.get("properties", {}))


def test_ai_answers_carry_a_source_and_a_list_of_cited_sources():
    schemas = c.DOC["components"]["schemas"]
    for name in ("SayItResponse", "ConversationGuide"):
        assert {"source", "sources"} <= set(schemas[name]["required"]), name
    assert schemas["AiSource"]["enum"] == ["mock", "groq", "rules"]


def test_the_ai_helpers_are_limited_to_the_right_roles():
    ops = c.operation_by_id()
    assert ops["ai_say_it_for_me"][2]["x-roles"] == ["woman"]
    assert ops["ai_conversation_guide"][2]["x-roles"] == ["partner", "supporter"]


def test_there_are_sixteen_voivodeships():
    assert len(c.DOC["components"]["schemas"]["Voivodeship"]["enum"]) == 16


def test_account_security_answers_never_depend_on_the_address():
    ops = c.operation_by_id()
    for operation_id in ("signup", "resend_activation", "request_password_reset"):
        statuses = set(ops[operation_id][2]["responses"])
        assert statuses == {"202", "422"}, operation_id
        example = json.loads((c.EXAMPLES_DIR / f"{operation_id}.202.json").read_text("utf-8"))
        assert example == {"status": "ok"}


def test_release_task_needs_an_active_group_like_the_other_task_changes():
    op = c.operation_by_id()["release_task"][2]
    assert op["x-requires-active-group"] is True
