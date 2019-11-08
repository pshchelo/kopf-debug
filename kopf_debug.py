import asyncio
import functools
import time

import kopf

N_HANDLERS=5

@kopf.on.resume("zalando.org", "v1", "kopfexamples")
@kopf.on.update("zalando.org", "v1", "kopfexamples")
@kopf.on.create("zalando.org", "v1", "kopfexamples")
async def ensure(body, logger, event, **kwargs):
    fns = {s: functools.partial(dummy, s) for s in range(N_HANDLERS)}
    await kopf.execute(fns=fns)
    return {"message": f"{event}d"}

async def dummy(s, logger, event, **kwargs):
    logger.info(f"Handler {s} handles event {event}")
    await asyncio.sleep(N_HANDLERS-s)
    logger.info(f"Handler {s} took {N_HANDLERS - s}s to complete")
