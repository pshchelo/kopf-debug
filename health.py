from dataclasses import dataclass
import logging
from typing import Optional

import kopf

LOG = logging.getLogger(__name__)
# Example of deployment status field
# note that the 'status.observedGeneration' is changing almost like every second or
# two so it is impractical to listen on it, that's why the example below only
# subscribes for 'status.conditions' field and uses some heuristic to derive the cause
# of status change
"""
{'observedGeneration': 265,
 'replicas': 3,
 'updatedReplicas': 3,
 'readyReplicas': 3,
 'availableReplicas': 3,
 'conditions': [
    {'type': 'Progressing',
     'status': 'True',
     'lastUpdateTime': '2019-11-26T14:06:37Z',
     'lastTransitionTime': '2019-11-26T14:06:31Z',
     'reason': 'NewReplicaSetAvailable',
     'message': 'ReplicaSet "test-deploy-647c557884" has successfully progressed.'
},
   {'type': 'Available',
    'status': 'True',
    'lastUpdateTime': '2019-11-26T14:10:28Z',
    'lastTransitionTime': '2019-11-26T14:10:28Z',
    'reason': 'MinimumReplicasAvailable',
    'message': 'Deployment has minimum availability.'
}
]
}
"""

@dataclass(frozen=True)
class DeplCondition:
    status: str
    type: str
    reason: str
    message: str
    lastUpdateTime: str
    lastTransitionTime: str


@dataclass(frozen=True)
class StsStatus:
    observedGeneration: int
    replicas: int
    readyReplicas: int
    currentRevision: str
    updateRevision: str  # optional?
    collisionCount: int
    updatedReplicas: int = 0
    currentReplicas: int = 0

@dataclass(frozen=True)
class DsStatus:
    currentNumberScheduled: int
    numberMisscheduled: int
    desiredNumberScheduled: int
    numberReady: int
    observedGeneration: int
    numberAvailable: int
    numberUnavailable: int = 0
    updatedNumberScheduled: int = 0


def ident(meta):
    name = meta["name"]
    application = meta.get("labels", {}).get("application", name)
    component = meta.get("labels", {}).get("component", name)
    # single out prometheus-exported Deployments
    if application.startswith("prometheus") and component == "exporter":
        application = "prometheus-exporter"
        # examples:
        # name=openstack-barbican-rabbitmq-rabbitmq-exporter
        # name=openstack-memcached-memcached-exporter
        # name=prometheus-mysql-exporter
        prefix, component, *parts = name.split("-")
        if parts[0] == "rabbitmq" and component != "rabbitmq":
            component += "-rabbitmq"
    # single out rabbitmq StatefulSets
    # examples:
    # name=openstack-nova-rabbitmq-rabbitmq
    # name=openstack-rabbitmq-rabbitmq
    elif application == "rabbitmq" and component == "server":
        prefix, service, *parts = name.split("-")
        if service != "rabbitmq":
            application = service
            component = "rabbitmq"
    # single out openvswitch DaemonSets
    elif application == "openvswitch":
        # example:
        # name=openvswitch-db component=openvswitch-vswitchd-db
        component = "-".join(component.split("-")[1:])

    return application, component


@kopf.on.field("apps", "v1", "deployments", field="status.conditions")
async def dp(name, meta, new, **kwargs):
    LOG.info(f"{new}")
    application, component = ident(meta)
    conds = [DeplCondition(**c) for c in new]
    for c in conds:
        if c.type == "Available":
            avail_cond = c
        elif c.type == "Progressing":
            progr_cond = c
    if avail_cond.status == "True" and (
        progr_cond.status == "True"
        and progr_cond.reason == "NewReplicaSetAvailable"
    ):
        status = "Ready"
    elif avail_cond.status == "False":
        status = "Unhealthy"
    elif progr_cond.reason == "ReplicaSetUpdated":
        status = "Progressing"
    else:
        status = "Unknown"
    patch = {"health": {application: {component: status}}}
    LOG.info(
        f"[WATCH-ME] Deployment for {application}/{component} "
        f"is {status}"
    )


@kopf.on.field("apps", "v1", "statefulsets", field="status")
async def sts(name, meta, new, **kwargs):
    LOG.info(f"{new}")
    application, component = ident(meta)
    st = StsStatus(**new)
    status = "Unknown"
    if st.updateRevision:
        # updating, created new ReplicaSet
        if st.currentRevision == st.updateRevision:
            if st.replicas == st.readyReplicas == st.currentReplicas:
                status = "Ready"
            else:
                status = "Unhealthy"
        else:
            status = "Progressing"
    else:
        if st.replicas == st.readyReplicas == st.currentReplicas:
            status = "Ready"
        else:
            status = "Unhealthy"
    patch = {"health": {application: {component: status}}}
    LOG.info(
        f"[WATCH-ME] StatefulSet for {application}/{component} "
        f"is {status}"
    )


@kopf.on.field("apps", "v1", "daemonsets", field="status")
async def ds(name, meta, new, **kwargs):
    LOG.info(f"{new}")
    application, component = ident(meta)
    status = "Unknown"
    st = DsStatus(**new)
    if (st.currentNumberScheduled ==
        st.desiredNumberScheduled ==
        st.numberReady ==
        st.updatedNumberScheduled ==
        st.numberAvailable):
            if not st.numberMisscheduled:
                status = "Ready"
            else:
                status = "Progressing"
    elif st.updatedNumberScheduled < st.desiredNumberScheduled:
        status = "Progressing"
    elif st.numberReady < st.desiredNumberScheduled:
        status = "Unhealthy"
    patch = {"health": {application: {component: status}}}
    LOG.info(
        f"[WATCH-ME] DaemonSet for {application}/{component} "
        f"is {status}"
    )
