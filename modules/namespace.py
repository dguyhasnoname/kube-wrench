"""[Module to namespace details]"""
import kubernetes.client
from kubernetes.client.rest import ApiException


class NameSpaceWrench:
    """
    Class to check namespace details in cluster
    """

    def __init__(self, k8s_config, logger):
        self.k8s_config = k8s_config
        self.logger = logger
        with kubernetes.client.ApiClient(k8s_config) as api_client:
            self.core = kubernetes.client.CoreV1Api(api_client)

    def get_ns_list(self):
        """[Get namespace list]

        Returns:
            [list]: [List of namespaces]
        """
        self.logger.debug("Fetching namespace list in the cluster.")
        try:
            ns_list = self.core.list_namespace(timeout_seconds=10)
            return ns_list
        except ApiException as exp:
            self.logger.warning(
                "Exception when calling CoreV1Api->list_namespace: %s", exp
            )
            return None

    def get_ns_events(self, namespace, pod_name):
        """[Get namespace events]

        Args:
            namespace ([str]): [Namespace name]

        Returns:
            [list]: [list of namespace events]
        """
        self.logger.debug("Fetching namespace events in the cluster.")
        try:
            ns_events = self.core.list_namespaced_event(namespace, timeout_seconds=10)
        except ApiException as exp:
            self.logger.warning(
                "Exception when calling CoreV1Api->list_namespaced_event: %s", exp
            )
            return None

        if ns_events.items:
            for event in ns_events.items:
                if not "Normal" in event.type and event.involved_object.name in pod_name:
                    self.logger.warning(
                        "Event related: %s %s %s/%s. Message: %s. Node: %s",
                        event.reason,
                        event.involved_object.kind,
                        event.involved_object.namespace,
                        event.involved_object.name,
                        event.message,
                        event.reporting_instance,
                    )
                else:
                    self.logger.debug(
                        "Event: %s %s %s/%s. Message: %s. Node: %s",
                        event.reason,
                        event.involved_object.kind,
                        event.involved_object.namespace,
                        event.involved_object.name,
                        event.message,
                        event.reporting_instance,
                    )
        else:
            self.logger.info(
                "No events found in %s namespace for the cluster.", namespace
            )
        return ns_events

    def namespace_wrench(self):
        """[Process namespace details and events]

        Returns:
            [list]: [List of namespace details]
        """
        ns_list = self.get_ns_list()
        if ns_list:
            for ns_name in ns_list.items:
                self.logger.info(
                    "Namespace: %s, Status: %s",
                    ns_name.metadata.name,
                    ns_name.status.phase,
                )
        else:
            self.logger.warning("No namespace found in the cluster.")
        return ns_list
