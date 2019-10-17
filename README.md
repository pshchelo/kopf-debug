# Minimal kopf-based operator for debugging

## Usage

```
kubectl apply -f deploy
tox
```

Default tox env is `kopf` which installs latest kopf release from PyPI.
Alternatively one can use `tox -ekopf-master` that will install kopf
from HEAD of master branch on GitHub.
