import kopf

@kopf.on.create("", "v1", "secrets", labels={"foo": "bar"})
@kopf.on.update("", "v1", "secrets", labels={"foo": "bar"})
def apply(name, logger, event, **kwargs):
    logger.info(f"Event {event} for secret {name}")
