"""Concurrent requests must queue up on SQLite, not fail with "database is locked"."""

import threading

import pytest
from django.conf import settings
from django.db import connections

from .helpers import Api

pytestmark = pytest.mark.django_db(transaction=True)


def test_every_transaction_takes_the_write_lock_first():
    assert settings.DATABASES["default"]["OPTIONS"]["transaction_mode"] == "IMMEDIATE"


def test_simultaneous_sign_ups_both_get_the_same_answer(db):
    barrier = threading.Barrier(2)
    answers = []

    def sign_up(number):
        try:
            browser = Api()
            browser.csrf_token()
            barrier.wait()
            body = {
                "email": f"ola{number}@example.com",
                "password": "tajne-haslo-1",
                "display_name": f"Ola {number}",
            }
            answers.append(browser.call("signup", body=body, check=False).status)
        finally:
            connections.close_all()

    for _ in range(5):
        answers.clear()
        threads = [threading.Thread(target=sign_up, args=(n,)) for n in range(2)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()
        assert answers == [202, 202]
