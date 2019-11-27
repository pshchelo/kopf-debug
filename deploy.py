from dataclasses import dataclass
import logging

import kopf

LOG = logging.getLogger(__name__)
# Example of deployment status field
# note that the 'observedGeneration' is changing almost like every second or
# two so it is impractical to listen on it, that's why the example below only
# subscribes for 'conditions' field and uses some heuristic to derive the cause
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

@dataclass
class DeplCondition:
    status: str
    type: str
    reason: str
    message: str
    lastUpdateTime: str
    lastTransitionTime: str


@kopf.on.field("apps", "v1", "deployments", field="status.conditions")
async def watch_deployment_status(name, meta, new, **kwargs):
    LOG.debug(f"{new}")
    application = meta["labels"].get("application", name)
    component = meta["labels"].get("component", name)
    conds = [DeplCondition(**c) for c in new]
    for c in conds:
        if c.type == 'Available':
            avail_cond = c
        elif c.type == 'Progressing':
            progr_cond = c
    if (avail_cond.status == 'True' and
            (progr_cond.status == 'True' and progr_cond.reason == 'NewReplicaSetAvailable')):
        depl_status = 'Ready'
    elif avail_cond.status == 'False':
        depl_status = 'Unhealthy'
    elif progr_cond.reason == 'ReplicaSetUpdated':
        depl_status = "Progressing"
    else:
        depl_status = "Unknown"
    patch = {application: {component: depl_status}}
    LOG.info(f"[WATCH-ME] Deployment for {application}/{component} is {depl_status}")
