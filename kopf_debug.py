import asyncio
import functools
import random
import time

import kopf
import pykube


api = pykube.HTTPClient(pykube.KubeConfig.from_env())
KopfChild = pykube.object_factory(api, "zalando.org/v1", "KopfChild")


# @kopf.on.resume("zalando.org", "v1", "kopfexamples", labels={"foo": "bar"})
# @kopf.on.update("zalando.org", "v1", "kopfexamples", labels={"foo": "bar"})
# @kopf.on.create("zalando.org", "v1", "kopfexamples", labels={"foo": "bar"})
# @kopf.on.resume("zalando.org", "v1", "kopfexamples")
@kopf.on.update("zalando.org", "v1", "kopfexamples")
@kopf.on.create("zalando.org", "v1", "kopfexamples")
async def ensure(body, logger, event, **kwargs):
    fns = {"sleepy": sleepy}
    await kopf.execute(fns=fns)
    return {"message": f"{event}d"}


async def sleepy(logger, event, namespace, name, body, spec, **kwargs):
    logger.info(f"Handling event {event}")
    snooze = 10 * random.choice((0, 1))
    if snooze:
        logger.info(f"Will sleep for {snooze}s")
        # await asyncio.sleep(snooze)
        # time.sleep(snooze)
        raise kopf.TemporaryError("BOOM!")

    child_def = {
        "kind": "KopfChild",
        "apiVersion": "zalando.org/v1",
        "spec": body["spec"],
        "metadata": {
            "name": name,
            "namespace": namespace,
        },
    }
    logger.info(f"Applying spec with value {spec['field']}")
    try:
        child = KopfChild.objects(api).filter(namespace=namespace).get(name=name)
        child.set_obj(child_def)
        child.update()
    except pykube.ObjectDoesNotExist:
        child = KopfChild(api, child_def)
        child.create()
