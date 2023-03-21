from __future__ import annotations

from tests.conftest import Role, User, UserToRole


async def test_insert(manager, transaction):
    res = await manager.run(User.select())
    assert not res

    await manager.run(User.insert(name="Mickey"))
    [user] = await manager.run(User.select())
    assert user
    assert user.id
    assert user.name == "Mickey"

    await manager.run(Role.insert(name="admin"))
    [role] = await manager.run(Role.select())
    assert role
    assert role.id
    assert role.name == "admin"

    await manager.run(UserToRole.insert(role=role, user=user))
    [user_to_role] = await manager.run(UserToRole.select())
    assert user_to_role


async def test_insert_many(manager, transaction):
    query = User.insert_many(
        [
            {"name": "Mickey"},
            {"name": "John"},
        ],
    )
    last_id = await manager.run(query)
    assert last_id is not None

    [user1, user2] = await manager.run(User.select().order_by(User.id))
    assert user1
    assert user2
    assert user1.name == "Mickey"
    assert user2.name == "John"


async def test_create(manager, transaction):
    user = await manager.create(User, name="Mickey")
    assert user
    assert user.id
    assert user.name == "Mickey"


async def test_create_uid(manager, transaction):
    from uuid import UUID

    role = await manager.create(Role, name="admin")
    assert role
    assert role.id
    assert UUID(str(role.id))


async def test_update(manager, transaction):
    await manager.create(User, name="Mickey")
    await manager.create(User, name="John")
    query = User.update(name="Timmy")
    upd = await manager.run(query)
    assert upd == 2
    user = await manager.get(User)
    assert user.name == "Timmy"


async def test_save(manager, transaction):
    res = await manager.run(User.select())
    assert not res

    user = User(name="Mickey")
    rows = await manager.save(user)
    assert rows
    assert user.id
    assert user.name == "Mickey"
    assert not user._dirty

    user.name = "John"
    assert user._dirty
    rows = await manager.save(user)
    assert rows
    assert user.id
    assert user.name == "John"
    assert not user._dirty

    user = await manager.get(User, id=user.id)
    assert user.name == "John"


async def test_delete(manager, transaction):
    source = await manager.create(User, name="Mickey")
    await manager.execute(User.delete())
    res = await manager.run(User.select())
    assert not res

    await manager.create(User, name="John")

    source = await manager.create(User, name="Mickey")
    await manager.delete_instance(source)
    res = await manager.get_or_none(User, User.id == source.id)
    assert res is None

    source = await manager.create(User, name="Mickey")
    await manager.delete_by_id(User, source.id)
    res = await manager.get_or_none(User, User.id == source.id)
    assert res is None

    assert await manager.run(User.select())
