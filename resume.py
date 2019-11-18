import kopf


@kopf.on.update("zalando.org", "v1", "kopfexamples")
@kopf.on.create("zalando.org", "v1", "kopfexamples")
async def handle_apply(**kwargs):
    ...


@kopf.on.delete("zalando.org", "v1", "kopfexamples")
async def handle_delete(**kwargs):
    ...


@kopf.on.resume("zalando.org", "v1", "kopfexamples")
async def handle_resume(logger, **kwargs):
    for k, v in kwargs.items():
        logger.info(f"kwarg {k} = {v}")
