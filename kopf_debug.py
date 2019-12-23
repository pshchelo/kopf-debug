import asyncio
import functools
import random
import time

import kopf
import pykube

N_HANDLERS = 5

api = pykube.HTTPClient(pykube.KubeConfig.from_env())
KopfChild = pykube.object_factory(api, "zalando.org/v1", "KopfChild")


# @kopf.on.resume("zalando.org", "v1", "kopfexamples", labels={"foo": "bar"})
# @kopf.on.update("zalando.org", "v1", "kopfexamples", labels={"foo": "bar"})
# @kopf.on.create("zalando.org", "v1", "kopfexamples", labels={"foo": "bar"})
# @kopf.on.resume("zalando.org", "v1", "kopfexamples")
@kopf.on.update("zalando.org", "v1", "kopfexamples")
@kopf.on.create("zalando.org", "v1", "kopfexamples")
async def ensure(body, logger, event, **kwargs):
    fns = {s: functools.partial(sleepy, s) for s in range(N_HANDLERS)}
    await kopf.execute(fns=fns)
    return {"message": f"{event}d"}


async def sleepy(s, logger, event, namespace, name, body, spec, **kwargs):
    logger.info(f"Handler {s} for event {event} with field {spec['field']}")
    # snooze = 10 * random.choice((0, 1))
    if event == "update" and s == 0 and spec['field'] == 'value1' and random.choice((True, False)):
        # logger.info(f"Will sleep for {snooze}s")
        # await asyncio.sleep(snooze)
        # time.sleep(snooze)
        raise kopf.TemporaryError("BOOM!")

    child_def = {
        "kind": "KopfChild",
        "apiVersion": "zalando.org/v1",
        "spec": body["spec"],
        "metadata": {
            "name": f"{name}.{s}",
        },
    }
    logger.info(f"Applying spec with value {spec['field']}")
    try:
        child = KopfChild.objects(api).filter(namespace=namespace).get(name=child_def["metadata"]["name"])
        kopf.adopt(child_def, body)
        child.set_obj(child_def)
        child.update()
    except pykube.ObjectDoesNotExist:
        child = KopfChild(api, child_def)
        kopf.adopt(child_def, body)
        child.create()
