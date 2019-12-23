import functools
import kopf

N_HANDLERS = 5


@kopf.on.update("zalando.org", "v1", "kopfexamples")
@kopf.on.create("zalando.org", "v1", "kopfexamples")
async def ensure(body, logger, event, **kwargs):
    fns = {s: functools.partial(handle, s) for s in range(N_HANDLERS)}
    await kopf.execute(fns=fns)
    return {"message": f"{event}d"}


async def handle(s, logger, event, spec, **kwargs):
    logger.info(f"Handler {s} for event {event} with field {spec['field']}")
