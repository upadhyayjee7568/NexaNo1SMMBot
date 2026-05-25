from app.core.rbac import ROLE_LEVEL


def test_role_hierarchy():
    assert ROLE_LEVEL['superadmin'] > ROLE_LEVEL['admin'] > ROLE_LEVEL['support'] > ROLE_LEVEL['user']
