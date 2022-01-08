"""[Module to process pods]"""
import kubernetes.client
from kubernetes.client.rest import ApiException
from .output import Output
from .containers import ContainerWrench
from .resource_quota import ResourceQuotaWrench

class PodWrench:
    """
    Check pod status and log details
    """

    def __init__(self, k8s_config, namespace, logger):
        self.k8s_config = k8s_config
        self.namespace = namespace
        self.logger = logger
        with kubernetes.client.ApiClient(k8s_config) as api_client:
            self.core = kubernetes.client.CoreV1Api(api_client)

    def get_pods(self):
        """[Get all pods in the namespace]

        Returns:
            [list]: [List of pods]
        """
        try:
            self.logger.info("Fetching %s namespace pods data.", self.namespace)
            pods = self.core.list_namespaced_pod(self.namespace, timeout_seconds=10)
            self.logger.info("Fetched pod data for namespace %s", self.namespace)
            # self.logger.debug("Pod details: %s", pods)
            return pods
        except ApiException as exp:
            self.logger.warning(
                "Exception when calling CoreV1Api->list_pod_for_namespace %s: %s",
                self.namespace,
                exp,
            )
            return None

    def pod_pvc_status(self, pod):
        """[Get PVC status for the pod]

        Args:
            pod ([dict]): [Pod details in dict]

        Returns:
            [list]: [PVC status for the pod]
        """
        pod_pvc_chk_result = []
        if pod.spec.volumes:
            for volume in pod.spec.volumes:
                if volume.persistent_volume_claim:
                    pod_name = pod.metadata.name
                    claim_name = volume.persistent_volume_claim.claim_name
                    self.logger.info(
                        "Checking PVC %s status for pod: %s/%s ",
                        claim_name,
                        self.namespace,
                        pod_name,
                    )
                    pvc_status = self.core.read_namespaced_persistent_volume_claim(
                        claim_name, self.namespace
                    )
                    if pvc_status.status.phase == "Bound":
                        self.logger.info(
                            "PVC %s is in Bound state for pod: %s/%s.",
                            self.namespace,
                            pod.metadata.name,
                            claim_name,
                        )
                    else:
                        self.logger.warning(
                            "PVC %s is in %s state for pod: %s/%s.",
                            self.namespace,
                            pvc_status.status.phase,
                            pod.metadata.name,
                            claim_name,
                        )
                    pod_pvc_chk_result.append(
                        [pod_name, claim_name, pvc_status.status.phase]
                    )
        else:
            self.logger.info(
                "Pod %s/%s does not have any PVC.", self.namespace, pod.metadata.name
            )
        return pod_pvc_chk_result

    def pod_node_status(self, pod):
        """[Get node allocation status for the pod]

        Args:
            pod ([dict]): [Pod details in dict]

        Returns:
            [list]: [Node allocation status for the pod]
        """
        pod_node_chk_result = []
        self.logger.info(
            "Checking if pod %s/%s is allocated a node or not.",
            self.namespace,
            pod.metadata.name,
        )
        if pod.spec.node_name:
            self.logger.info(
                "Pod %s/%s is scheduled on node %s.",
                self.namespace,
                pod.metadata.name,
                pod.spec.node_name,
            )
            pod_node_chk_result.append(
                [pod.metadata.name, pod.spec.node_name, "NODE_ALLOCATED"]
            )
        else:
            self.logger.warning(
                "Pod %s/%s is not scheduled on any node. Please check scheduler for issues.",
                self.namespace,
                pod.metadata.name,
            )
            for status in pod.status.conditions:
                self.logger.warning(
                    "Pod %s/%s is in %s state. Message: %s.",
                    self.namespace,
                    pod.metadata.name,
                    status.reason,
                    status.message,
                )
            pod_node_chk_result.append(
                [pod.metadata.name, pod.spec.node_name, "NODE_NOT_ALLOCATED"]
            )
        return pod_node_chk_result

    def check_pod_status(self, pod):
        """[Get status of a pod in a namespace]

        Args:
            pod ([dict]): [Pod object]

        Returns:
            [list]: [Pod status]
        """
        pod_status = pod.status.phase
        container = ContainerWrench(self.k8s_config, self.namespace, self.logger)
        quota = ResourceQuotaWrench(self.k8s_config, self.namespace, self.logger)
        if pod_status == "Running":
            self.logger.info(
                "Pod %s/%s is in %s phase.", self.namespace, pod.metadata.name, pod_status
            )
            container.container_wrench(pod)
        elif pod_status in ["Pending", "Failed", "Unknown"]:
            self.logger.warning(
                "Pod %s/%s is in %s phase.", self.namespace, pod.metadata.name, pod_status
            )
            if PodWrench.pod_node_status(self, pod):
                PodWrench.pod_pvc_status(self, pod)
                ResourceQuotaWrench.resource_quota_wrench(self)
                container.container_wrench(pod)
        elif pod_status == "Succeeded":
            self.logger.info(
                "Pod %s/%s is in Completed phase.", self.namespace, pod.metadata.name
            )
        else:
            self.logger.error(
                "Pod %s/%s status is Invalid.", self.namespace, pod.metadata.name
            )
            pod_status = "Invalid"
        pod_status_chk = [pod.metadata.name, pod_status]
        return pod_status_chk

    def pod_wrench(self):
        """[Get status of all pods in a namespace]"""
        pods = PodWrench.get_pods(self)
        if pods:
            for pod in pods.items:
                self.logger.debug(
                    "Checking status of pod: %s/%s ", self.namespace, pod.metadata.name
                )
                PodWrench.check_pod_status(self, pod)
