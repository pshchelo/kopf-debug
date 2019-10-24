import asyncio
import functools
import time

import kopf

@kopf.on.create("zalando.org", "v1alpha1", "kopfdebugs")
async def create(body, logger, event, **kwargs):
    # fns = {s: functools.partial(dummy, s) for s in range(10)}
    # await kopf.execute(fns=fns)
    await dummy(9, logger, event)
    return {"message": "created"}

@kopf.on.update("zalando.org", "v1alpha1", "kopfdebugs")
async def update(*body, logger, event, **kwargs):
    # fns = {s: functools.partial(dummy, s) for s in range(10)}
    # await kopf.execute(fns=fns)
    await dummy(9, logger, event)
    return {"message": "updated"}

@kopf.on.resume("zalando.org", "v1alpha1", "kopfdebugs")
async def resume(body, logger, event, **kwargs):
    # fns = {s: functools.partial(dummy, s) for s in range(10)}
    # await kopf.execute(fns=fns)
    import pdb; pdb.set_trace()  # XXX BREAKPOINT
    await dummy(9, logger, event)
    return {"message": "resumed"}

async def dummy(s, logger, event, **kwargs):
    logger.info(f"Got event {event}")
    await asyncio.sleep(10-s)
    # time.sleep(10-s)
    logger.info(f"slept for {10 - s}")
