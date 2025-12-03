import logging
import kopf
import kubernetes

# Configure Python logging globally
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    handlers=[logging.StreamHandler()]
)

# Dedicated logger for operator patch actions
oplogger = logging.getLogger("probe-fix")

@kopf.on.startup()
def configure(settings: kopf.OperatorSettings, **_):
    # Disable automatic posting of handler lifecycle events to Kubernetes
    settings.posting.enabled = False

    # Silence Kopf’s internal lifecycle logs (like "Handler succeeded")
    import logging as pylogging
    pylogging.getLogger("kopf.objects").setLevel(pylogging.WARNING)

    # Watch all namespaces
    settings.watching.namespaces = None
    # Load in-cluster config
    kubernetes.config.load_incluster_config()

    # Log once when operator starts
    logging.info("Operator restarted and resumed watching resources")

@kopf.on.resume('apps', 'v1', 'deployments')
@kopf.on.resume('apps', 'v1', 'statefulsets')
def activate_timer_on_resume(**kwargs):
    # Log which resource is resumed
    logging.info(f"Resumed watching {kwargs.get('name')} in ns={kwargs.get('namespace')}")

@kopf.on.create('apps', 'v1', 'deployments')
@kopf.on.create('apps', 'v1', 'statefulsets')
def activate_timer_on_create(spec, name, namespace, body, **kwargs):
    # Immediate probe patching for new workloads
    patch_probe_timeout(spec, name, namespace, body)

def patch_controller(api, kind, name, namespace, patch, body, changes):
    if kind == 'Deployment':
        api.patch_namespaced_deployment(name, namespace, patch)
    elif kind == 'StatefulSet':
        api.patch_namespaced_stateful_set(name, namespace, patch)

    # Log once summarizing all changes
    oplogger.info(
        f"Patched {kind} '{name}' in ns={namespace}: {', '.join(changes)}"
    )

    # Emit one concise Kubernetes event
    kopf.event(
        body,
        type="Normal",
        reason="Patched",
        message=f"{kind}/{name} ns={namespace}: {', '.join(changes)} updated"
    )

@kopf.timer('apps', 'v1', 'deployments', interval=30.0)
@kopf.timer('apps', 'v1', 'statefulsets', interval=30.0)
def patch_probe_timeout(spec, name, namespace, body, **_):
    api = kubernetes.client.AppsV1Api()
    original_containers = spec.get('template', {}).get('spec', {}).get('containers', [])
    patched_containers = []
    changes = []

    for container in original_containers:
        container_patch = {"name": container["name"]}
        for probe_type in ['livenessProbe', 'readinessProbe']:
            probe = container.get(probe_type)
            if probe and probe.get('timeoutSeconds') == 1:
                container_patch[probe_type] = {**probe, "timeoutSeconds": 5}
                changes.append(f"{probe_type} in container '{container['name']}'")
        if len(container_patch) > 1:
            patched_containers.append(container_patch)

    if patched_containers:
        patch = {"spec": {"template": {"spec": {"containers": patched_containers}}}}
        patch_controller(api, body['kind'], name, namespace, patch, body, changes)
