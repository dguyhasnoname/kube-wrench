"""[Module to process service details]"""
import kubernetes.client
from kubernetes.client.rest import ApiException
from .ingress import IngressWrench


class ServiceWrench:
    """[Class to get service details]"""

    def __init__(self, k8s_config, namespace, logger):
        self.k8s_config = k8s_config
        self.namespace = namespace
        self.logger = logger
        with kubernetes.client.ApiClient(k8s_config) as api_client:
            self.core = kubernetes.client.CoreV1Api(api_client)

        self.logger.debug("Fetching %s namespace services data.", self.namespace)
        try:
            self.services = self.core.list_namespaced_service(
                self.namespace, timeout_seconds=10
            )
        except ApiException as exp:
            self.logger.warning(
                "Exception when calling CoreV1Api->list_namespaced_service: %s", exp
            )

    def svc_type_check(self, svc, svc_mapped_to_pod, pod):
        """[Check service type]

        Args:
            svc ([dict]): [Service object in dict]
            svc_mapped_to_pod ([str]): [Service name mapped to pod]
            pod ([dict]): [Pod object in dict]
        """
        svc_type = svc.spec.type
        if "ClusterIP" in svc_type:
            svc_detail = svc.spec.cluster_ip
        if "LoadBalancer" in svc_type:
            svc_detail = svc.status.load_balancer.ingress[0].hostname
        if "NodePort" in svc_type:
            svc_detail = svc.spec.ports[0].node_port
        if "ExternalName" in svc_type:
            svc_detail = svc.spec.external_name
        self.logger.info(
            "Service %s is mapped to pod %s/%s. %s: %s",
            svc_mapped_to_pod,
            self.namespace,
            pod.metadata.name,
            svc_type,
            svc_detail,
        )

    def service_wrench(self, pod):
        """[Get service details for the pod]

        Args:
            pod ([dict]): [Pod details in dict]
        """
        self.logger.debug(
            "Analyzing service mapped to pod %s/%s.", self.namespace, pod.metadata.name
        )
        svc_mapped_to_pod = ""
        for svc in self.services.items:
            mapping = []
            try:
                for selector_name in svc.spec.selector:
                    try:
                        if (
                            svc.spec.selector[selector_name]
                            in pod.metadata.labels[selector_name]
                        ):
                            mapping.append(True)
                        else:
                            mapping.append(False)
                    except KeyError:
                        self.logger.debug(
                            "Label %s not found in pod %s.",
                            selector_name,
                            pod.metadata.name,
                        )
            except TypeError:
                self.logger.debug(
                    "No selector found in service %s.", svc.metadata.name
                )

            if all(mapping) and mapping:
                svc_mapped_to_pod = svc.metadata.name
                self.svc_type_check(svc, svc_mapped_to_pod, pod)
                IngressWrench(self.k8s_config, self.namespace, self.logger).ingress_wrench(svc)

        if not svc_mapped_to_pod:
            self.logger.info(
                "No service is mapped to pod %s/%s.", self.namespace, pod.metadata.name
            )
        return svc_mapped_to_pod
