import pytest
import asyncio
import os
import rethinkdb as r

from brink import fields, models
from brink.db import conn


r.set_loop_type("asyncio")
conn.setup({
    "host": os.environ.get("RETHINKDB_PORT_28015_TCP_ADDR", "localhost"),
})


class Turtle(models.Model):
    name = fields.CharField()


class Rabbit(models.Model):
    name = fields.CharField()
    buddy = fields.ReferenceField(Turtle)
    buddies = fields.ReferenceListField(Turtle)


async def get_first(model):
    return (await model.all().limit(1).as_list())[0]


@pytest.yield_fixture
def event_loop():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    yield loop
    loop.run_until_complete(conn.close())
    loop.close()


@pytest.mark.asyncio
async def test_setup_table():
    try:
        await r.table_create(Rabbit.table_name).run(await conn.get())
        await r.table_create(Turtle.table_name).run(await conn.get())
    except:
        pass
    finally:
        await conn.close()


@pytest.mark.asyncio
async def test_save():
    turtle = Turtle(name="Lars")
    model = Rabbit(name="test", buddy=turtle, buddies=[turtle])

    assert turtle.id is None
    assert model.id is None
    assert model.buddy.id is None

    await turtle.save()
    await model.save()

    assert turtle.id is not None
    assert model.id is not None
    assert model.buddy.id is not None


@pytest.mark.asyncio
async def test_fetch_all():
    models = await Rabbit.all().as_list()
    assert len(models) == 1


@pytest.mark.asyncio
async def test_fetch_one():
    id = (await get_first(Rabbit)).id
    model = await Rabbit.get(id)
    assert model.id == id


@pytest.mark.asyncio
async def test_update():
    model = await get_first(Rabbit)
    model.name = "New title"

    await model.save()

    model_after = await get_first(Rabbit)
    assert model.name == model_after.name


@pytest.mark.asyncio
async def test_resolve_reference():
    model = await get_first(Rabbit)
    assert model.buddy.id is not None


@pytest.mark.asyncio
async def test_resolve_reference_list():
    pass


@pytest.mark.asyncio
async def test_destroy_table():
    await r.table_drop(Rabbit.table_name).run(await conn.get())
    await r.table_drop(Turtle.table_name).run(await conn.get())
    await conn.close()
