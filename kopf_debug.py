import asyncio
import functools

import kopf


N_HANDLERS = 5


@kopf.on.resume("zalando.org", "v1", "kopfexamples", labels={"foo": "bar"})
@kopf.on.update("zalando.org", "v1", "kopfexamples", labels={"foo": "bar"})
@kopf.on.create("zalando.org", "v1", "kopfexamples", labels={"foo": "bar"})
async def ensure(body, logger, event, **kwargs):
    # fns = {s: functools.partial(dummy, s) for s in range(N_HANDLERS)}
    # await kopf.execute(fns=fns)
    fns = {asyncio.create_task(dummy(s, logger, event, **kwargs)): s
           for s in range(N_HANDLERS)}
    for f in asyncio.as_completed(fns.keys(), timeout=60):
        try:
            res = await f
        except Exception as e:
            raise e

    return {"message": f"{event}d"}


async def dummy(s, logger, event, **kwargs):
    logger.info(f"Handler {s} handles event {event}")
    await asyncio.sleep(N_HANDLERS-s)
    logger.info(f"Handler {s} took {N_HANDLERS - s}s to complete")
    if s == N_HANDLERS-1 and kwargs["retry"] == 0:
        raise kopf.TemporaryError(f"Handler {s} has to retry")
