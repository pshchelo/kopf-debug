import functools
import kopf

N_HANDLERS = 5


@kopf.on.update("zalando.org", "v1", "kopfexamples")
@kopf.on.create("zalando.org", "v1", "kopfexamples")
async def ensure(body, logger, event, **kwargs):
    fns = {s: functools.partial(handle, s) for s in range(N_HANDLERS)}
    for n, f in fns.items():
        await f(logger, event, body, **kwargs)
    # await kopf.execute(fns=fns)
    return {"message": f"{event}d"}


async def handle(s, logger, event, body, spec, **kwargs):
    if s == 1 and kwargs['retry'] == 0:
        raise kopf.TemporaryError(f"Handler {s} failed, will retry")
    logger.info(f"Handler {s} for event {event} with field {spec['field']}")
