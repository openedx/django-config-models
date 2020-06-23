"""
Define pytest hooks.
"""


from django import db


def pytest_runtest_setup(item):  # pylint: disable=unused-argument
    """
    Before any tests start, reset all django database connections.
    Used to make sure that tests running in multi processes aren't sharing
    a database connection.
    """
    for db_ in db.connections.all():
        db_.close()
