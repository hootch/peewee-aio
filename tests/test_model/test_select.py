import peewee
import pytest

from peewee_aio.model import AIOModel


async def test_select(TestModel: AIOModel, schema):
    await TestModel.delete()
    inst = await TestModel.create(data="data")

    assert [inst] == await TestModel.select().where(TestModel.id == inst.id)

    async for data in TestModel.select():
        assert data == inst

    assert await TestModel.select().exists()
    assert await TestModel.select().count() == 1
    assert await TestModel.select().get() == inst
    assert await TestModel.select().peek() == inst
    assert await TestModel.select().first() == inst
    assert await TestModel.select(peewee.fn.MAX(TestModel.id)).scalar()


async def test_select_items(TestModel, schema):
    await TestModel.insert_many([dict(data=f"t{n}") for n in range(3)])
    qs = TestModel.select()
    t1 = await qs[0]
    assert t1
    assert t1.data == "t0"

    t2 = await qs[1]
    assert t2
    assert t2.data == "t1"

    res = await qs[0:2]
    assert res
    assert res == [t1, t2]


async def test_get_or_create(TestModel, schema):

    with pytest.raises(peewee.DatabaseError):
        inst, created = await TestModel.get_or_create(defaults={})

    class TestModel(TestModel):
        async def save(self, **kwargs):
            self.data += "-custom"
            return await super().save(**kwargs)

    inst, created = await TestModel.get_or_create(data="data")
    assert inst
    assert inst.data == "data-custom"
    assert created

    inst2, created = await TestModel.get_or_create(data="data-custom")
    assert inst2 == inst
    assert not created


async def test_get(TestModel, schema):
    source = await TestModel.create(data="data")

    inst = await TestModel.get_or_none(TestModel.id == source.id)
    assert inst
    assert inst == source

    inst = await TestModel.get_or_none(TestModel.id == 999)
    assert inst is None

    inst = await TestModel.get(TestModel.id == source.id)
    assert inst
    assert inst == source

    inst = await TestModel.get_by_id(source.id)
    assert inst
    assert inst == source


async def test_prefetch(manager):
    class BaseModel(manager.Model):
        data = peewee.CharField()

    class RelModel(manager.Model):
        data = peewee.CharField()
        base = peewee.ForeignKeyField(BaseModel)

    await BaseModel.create_table(safe=True)
    await RelModel.create_table(safe=True)

    source = await BaseModel.create(data="data")
    res = await BaseModel.select().prefetch()
    assert res

    await RelModel.insert_many([dict(base=source, data=f"{n}") for n in range(3)])
    res = await BaseModel.select().prefetch(RelModel)
    assert res
    assert res[0].relmodel_set
    assert len(res[0].relmodel_set) == 3

    await RelModel.drop_table(safe=True)
    await BaseModel.drop_table(safe=True)


async def test_union(TestModel, schema):
    from peewee_aio.model import ModelCompoundSelectQuery

    await TestModel.delete()
    await TestModel.insert_many([TestModel(data=f"t{n}") for n in range(3)])

    qs = (
        TestModel.select().where(TestModel.data == "t1")
        | TestModel.select().where(TestModel.data == "t2")
        | TestModel.select().where(TestModel.data == "t3")
    )

    assert isinstance(qs, ModelCompoundSelectQuery)

    res = await qs.limit(2)
    assert res


async def test_scalar(TestModel, schema):
    await TestModel.delete()
    await TestModel.insert_many([TestModel(data=f"t{n}") for n in range(3)])
    assert await TestModel.select(TestModel.data).scalars() == ["t0", "t1", "t2"]

    assert await TestModel.select(TestModel.data).scalar() == "t0"
    assert await TestModel.select(TestModel.data).scalar(as_tuple=True) == ("t0",)
    assert await TestModel.select(TestModel.data).scalar(as_dict=True) == {"data": "t0"}


async def test_first(TestModel, schema):
    await TestModel.insert_many([TestModel(data=f"t{n}") for n in range(3)])
    qs = TestModel.select().order_by(TestModel.id)
    ts1, ts2, ts3 = await qs
    ts = await qs.first()
    assert ts == ts1
    assert (await qs) == [ts1, ts2, ts3]
