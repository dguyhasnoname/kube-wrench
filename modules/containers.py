"""[Module to process pod containers]"""
import kubernetes.client
from kubernetes.client.rest import ApiException


class ContainerWrench:
    """
    Check pod's container status and log details
    """

    def __init__(self, k8s_config, namespace, logger):
        self.k8s_config = k8s_config
        self.namespace = namespace
        self.logger = logger
        with kubernetes.client.ApiClient(k8s_config) as api_client:
            self.core = kubernetes.client.CoreV1Api(api_client)

    def container_secret_status(self, pod):
        """[Get status of all secrets in a container]

        Args:
            pod ([dict]): [Pod details in dict]

        Returns:
            [list]: [Secret status for the pod]
        """
        self.logger.debug("Checking pod %s secrets.", pod.metadata.name)
        pod_secret_chk_result, sec_chk = [], ""
        if pod.spec.volumes:
            for volume in pod.spec.volumes:
                if volume.secret:
                    secret_name = volume.secret.secret_name
                    self.logger.info(
                        "Checking secret %s existence for pod: %s/%s ",
                        secret_name,
                        self.namespace,
                        pod.metadata.name,
                    )
                    secret_list = self.core.read_namespaced_secret(
                        secret_name, self.namespace
                    )
                    for secret in secret_list.items:
                        if secret.metadata.name == secret_name:
                            self.logger.info(
                                "Secret %s found for pod: %s/%s ",
                                secret_name,
                                self.namespace,
                                pod.metadata.name,
                            )
                            sec_chk = "SECRET_FOUND"
                            break
                    pod_secret_chk_result.append(
                        [pod.metadata.name, secret_name, sec_chk]
                    )
        return pod_secret_chk_result

    def container_configmap_status(self, pod):
        """[Get status of all configmaps in a container]

        Args:
            pod ([dict]): [Pod details in dict]

        Returns:
            [list]: [Configmap status for the pod]
        """
        pod_configmap_chk_result, cm_chk = [], ""
        if pod.spec.volumes:
            for volume in pod.spec.volumes:
                if volume.config_map:
                    configmap_name = volume.config_map.name
                    self.logger.info(
                        "Checking configmap %s status for pod: %s/%s ",
                        configmap_name,
                        self.namespace,
                        pod.metadata.name,
                    )
                    configmap_list = self.core.read_namespaced_config_map(
                        configmap_name, self.namespace
                    )
                    for configmap in configmap_list.items:
                        if configmap.metadata.name == configmap_name:
                            self.logger.info(
                                "Configmap %s found for pod: %s/%s ",
                                configmap_name,
                                self.namespace,
                                pod.metadata.name,
                            )
                            cm_chk = "CONFIGMAP_FOUND"
                            break
                    pod_configmap_chk_result.append(
                        [pod.metadata.name, configmap_name, cm_chk]
                    )
        return pod_configmap_chk_result

    def get_container_logs(self, pod_name, container_name):
        """[Get logs of a pod]

        Args:
            pod_name ([string]): [Pod name]
            container_name ([string]): [Container name running in the pod]

        Returns:
            [string]: [Logs of the pod]
        """
        try:
            self.logger.debug("Fetching logs for pod %s/%s.", self.namespace, pod_name)
            logs = self.core.read_namespaced_pod_log(
                pod_name,
                self.namespace,
                container=container_name,
                follow=False,
                tail_lines=10,
            )
            if not logs:
                logs = self.core.read_namespaced_pod_log(
                    pod_name,
                    self.namespace,
                    container=container_name,
                    previous="previous",
                    follow=False,
                    tail_lines=10,
                )
            self.logger.info("Logs for pod %s/%s: %s", self.namespace, pod_name, logs)
        except ApiException as exp:
            self.logger.error(
                "Could not read logs for %s/%s in current or previous run. Exception: %s",
                self.namespace,
                pod_name,
                exp.reason,
            )
            logs = None
        return logs

    def container_terminated(self, container, pod):
        """[Check if the container is terminated]

        Args:
            pod ([dict]): [Pod details in dict]
            container ([dict]): [Container details in dict]
        Returns:
            [bool]: [True if the container is terminated]
        """
        try:
            if container.state.terminated:
                self.logger.warning(
                    "Container %s terminated at %s due to %s with exit code: %s.",
                    container.name,
                    container.state.terminated.finished_at,
                    container.state.terminated.reason,
                    container.state.terminated.exit_code,
                )
                if "OOMKilled" in container.state.terminated.reason:
                    self.logger.warning(
                        "Please check resource allocation. Container %s in pod %s/%s "
                        "termination reason: OOMKilled.  Message: %s",
                        container.name,
                        self.namespace,
                        pod.metadata.name,
                        container.state.terminated.message,
                    )
                if "ContainerCannotRun" in container.state.terminated.reason:
                    self.logger.warning(
                        "Please check configurations inside the container image. Container %s in "
                        "pod %s/%s termination reason: ContainerCannotRun. Message: %s",
                        container.name,
                        self.namespace,
                        pod.metadata.name,
                        container.state.terminated.message,
                    )
                if "DeadlineExceeded" in container.state.terminated.reason:
                    self.logger.warning(
                        "Timeout may be the possible reason. Container %s in pod %s/%s"
                        " termination reason: DeadlineExceeded.  Message: %s",
                        container.name,
                        self.namespace,
                        pod.metadata.name,
                        container.state.terminated.message,
                    )
                if "Error" in container.state.terminated.reason:
                    self.logger.warning(
                        "Issue in container image. Container %s in pod %s/%s "
                        "termination reason: Error. Message: %s",
                        container.name,
                        self.namespace,
                        pod.metadata.name,
                        container.state.terminated.message,
                    )
                if "Completed" in container.state.terminated.reason:
                    self.logger.info(
                        "Container %s in pod %s/%s completed its run and shut down.",
                        container.name,
                        self.namespace,
                        pod.metadata.name,
                    )
        except KeyError:
            self.logger.warning(
                "Container %s is in Unknown state for pod %s/%s.",
                container.name,
                self.namespace,
                pod.metadata.name,
            )

    def container_waiting(self, container, pod):
        """[Check if the container is waiting]

        Args:
            container ([type]): [Container details in dict]
            pod ([type]): [Pod details in dict]
        """
        try:
            if container.state.waiting:
                self.logger.warning(
                    "Container %s waiting in %s status. Restart count: %s.",
                    container.name,
                    container.state.waiting.reason,
                    container.restart_count,
                )
                # container first goes in ErrImagePull and then ImagePullBackOff state
                if container.state.waiting.reason in [
                    "ImagePullBackOff",
                    "ErrImagePull",
                    "ErrImageNeverPull",
                ]:
                    self.logger.warning(
                        "Failed pulling the image %s for container %s in pod %s/%s. Message: %s",
                        container.image,
                        container.name,
                        self.namespace,
                        pod.metadata.name,
                        container.state.waiting.message,
                    )
                    if not pod.spec.image_pull_secrets:
                        self.logger.warning(
                            "No image pull secrets defined for pod %s/%s.",
                            self.namespace,
                            pod.metadata.name,
                        )
                    for cont in pod.spec.containers:
                        if (
                            cont.name in container.name
                            and "Never" in cont.image_pull_policy
                        ):
                            self.logger.warning(
                                "Image pull policy is set to %s for container %s",
                                cont.image_pull_policy,
                                cont.name,
                            )
                if "RegistryUnavailable" in container.state.waiting.reason:
                    self.logger.warning(
                        "Unable to connect to the image registry for container %s.",
                        container.name,
                    )
                if "InvalidImageName" in container.state.waiting.reason:
                    self.logger.warning(
                        "Invalid image name %s for container %s in pod %s/%s. Message: %s",
                        container.image,
                        container.name,
                        self.namespace,
                        pod.metadata.name,
                        container.state.waiting.message,
                    )
                if "CreateContainerConfigError" in container.state.waiting.reason:
                    self.logger.warning(
                        "Unable to create the container configuration used by kubelet. "
                        "Error creating container %s in pod %s/%s.  Message: %s",
                        container.name,
                        self.namespace,
                        pod.metadata.name,
                        container.state.waiting.message,
                    )
                if container.state.waiting.reason in [
                    "RunContainerError",
                    "CreateContainerError",
                ]:
                    self.logger.warning(
                        "Possible issues: Mounting a not-existent volume e.g. ConfigMap or Secrets"
                        ", Mounting a read-only volume as read-write. Error while creating the "
                        "container %s in pod %s/%s. Message: %s",
                        container.name,
                        self.namespace,
                        pod.metadata.name,
                        container.state.waiting.message,
                    )
                    ContainerWrench.container_secret_status(self, pod)
                    ContainerWrench.container_configmap_status(self, pod)
                if "ContainerCreating" in container.state.waiting.reason:
                    self.logger.warning(
                        "Possibly awaiting for some other condition. Container %s is "
                        "creating in pod %s/%s. Message: %s",
                        container.name,
                        self.namespace,
                        pod.metadata.name,
                        container.state.waiting.message,
                    )
                if container.state.waiting.reason in [
                    "ImageInspectError",
                    "CrashLoopBackOff",
                ]:
                    if container.restart_count > 2:
                        self.logger.warning(
                            "Possible reason for CrashLoopBackOff status of Container %s in pod "
                            "%s/%s: misconfigured container image, error in the application or "
                            "Health probes failed too many times.",
                            container.name,
                            self.namespace,
                            pod.metadata.name,
                        )
                    ContainerWrench.get_container_logs(
                        self, pod.metadata.name, container.name
                    )
                if "NetworkPluginNotReady" in container.state.waiting.reason:
                    self.logger.warning("Network plugin not ready.")
                if "DockerDaemonNotReady" in container.state.waiting.reason:
                    self.logger.warning("Docker daemon not ready.")
                if "PreStartHookError" in container.state.waiting.reason:
                    self.logger.warning(
                        "preStart hook execution error for container %s in pod "
                        "%s/%s. Message: %s",
                        container.name,
                        self.namespace,
                        pod.metadata.name,
                        container.state.waiting.message,
                    )
                if "PostStartHookError" in container.state.waiting.reason:
                    self.logger.warning(
                        "postStart hook execution error for container %s in pod "
                        "%s/%s. Message: %s",
                        container.name,
                        self.namespace,
                        pod.metadata.name,
                        container.state.waiting.message,
                    )
        except KeyError:
            self.logger.warning(
                "Container %s is in Unknown state for pod %s/%s.",
                container.name,
                self.namespace,
                pod.metadata.name,
            )

    def container_wrench(self, pod):
        """[Get status of containers configured in a pod]

        Args:
            pod ([dict]): [Pod object]
        """
        pod_cont_status = pod.status.container_statuses
        try:
            for container in pod_cont_status:
                if container.ready:
                    self.logger.debug(
                        "Container %s is in ready state for pod %s/%s.",
                        container.name,
                        self.namespace,
                        pod.metadata.name,
                    )
                else:
                    self.logger.warning(
                        "Container %s is in NotReady state for pod %s/%s.",
                        container.name,
                        self.namespace,
                        pod.metadata.name,
                    )
                    # https://main.qcloudimg.com/raw/document/intl/product/pdf/457_35659_en.pdf
                    ContainerWrench.container_terminated(self, container, pod)
                    ContainerWrench.container_waiting(self, container, pod)
        except TypeError:
            self.logger.warning(
                "No running containers found in pod %s/%s.",
                self.namespace,
                pod.metadata.name,
            )
