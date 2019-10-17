import asyncio
import functools
import time

import kopf

@kopf.on.create("zalando.org", "v1alpha1", "kopfdebugs")
@kopf.on.update("zalando.org", "v1alpha1", "kopfdebugs")
@kopf.on.resume("zalando.org", "v1alpha1", "kopfdebugs")
async def apply(**kwargs):
    fns = {s: functools.partial(dummy, s) for s in range(10)}
    await kopf.execute(fns=fns)
    return {"message": "applied"}

def dummy(s, logger, event, **kwargs):
    logger.info(f"Got event {event}")
    # await asyncio.sleep(10-s)
    time.sleep(10-s)
    logger.info(f"slept for {10 - s}")
