"""[Module to get namespace quotas defined]"""
import kubernetes.client
from kubernetes.client.rest import ApiException
from .output import Output


class ResourceQuotaWrench:
    """[Class to process resource quota details]"""

    def __init__(self, k8s_config, namespace, logger):
        self.k8s_config = k8s_config
        self.namespace = namespace
        self.logger = logger
        with kubernetes.client.ApiClient(k8s_config) as api_client:
            self.core = kubernetes.client.CoreV1Api(api_client)

    def quota_usage_pctg(self, quota_used, quota_hard_limit, quota_name):
        """[Quota usage percentage]

        Args:
            quota_used ([str]): [Quota used]
            quota_hard_limit ([str]): [Quota hard limit set]

        Returns:
            [int]: [Quota usage percentage]
        """
        try:
            quota_usage_percentage = round((quota_used / quota_hard_limit * 100), 3)
            return quota_usage_percentage
        except ZeroDivisionError:
            self.logger.warning(
                "Quota hard limit is 0 for %s/%s", self.namespace, quota_name
            )
            return 0

    def quota_usage_status(
        self, quota_type, ns_quota_name, quota_used, quota_hard_limit
    ):
        """[Quota usage status]

        Args:
            quota_usage ([int]): [Quota usage percentage]
            quota_type ([str]): [Quota type]
            quota_name ([str]): [Quota name]
            used_quota ([str]): [Quota used]
            hard_quota ([str]): [Quota hard limit set]

        Returns:
            [list]: [Quota usage status]
        """
        quota_usage_status = []
        if "cpu" in quota_type:
            quota_usage = self.quota_usage_pctg(
                Output.convert_cpu(quota_used),
                Output.convert_cpu(quota_hard_limit),
                ns_quota_name,
            )
        elif "memory" in quota_type:
            quota_usage = self.quota_usage_pctg(
                Output.convert_memory(quota_used),
                Output.convert_memory(quota_hard_limit),
                ns_quota_name,
            )
        else:
            quota_usage = self.quota_usage_pctg(
                int(quota_used), int(quota_hard_limit), ns_quota_name
            )
        if quota_usage > 90:
            self.logger.warning(
                "ResourceQuota %s/%s %s is at %s percent. " "Used/Hard limit: %s/%s",
                self.namespace,
                ns_quota_name,
                quota_type,
                quota_usage,
                quota_used,
                quota_hard_limit,
            )
            quota_usage_status.append(
                [self.namespace, "high " + quota_type, quota_usage]
            )
        else:
            self.logger.info(
                "ResourceQuota %s/%s %s is at %s percent which is"
                " within threshold. Used/Hard limit: %s/%s",
                self.namespace,
                ns_quota_name,
                quota_type,
                quota_usage,
                quota_used,
                quota_hard_limit,
            )
        return quota_usage_status

    def resource_quota_wrench(self):
        """[Get quota status for the namespace]

        Returns:
            [list]: [Namespace quota status]
        """
        self.logger.debug(
            "Checking if namespace %s has resource limitation due to quota limits.",
            self.namespace,
        )
        self.logger.debug("Fetching %s namespace resource quota data.", self.namespace)
        quota_chk_result = []
        try:
            ns_quota_list = self.core.list_namespaced_resource_quota(self.namespace)
            if len(ns_quota_list.items) > 0:
                self.logger.info(
                    "%s resource quotas found in %s namespace. Checking for quota limits.",
                    len(ns_quota_list.items),
                    self.namespace,
                )
                for quota in ns_quota_list.items:
                    ns_quota_name = quota.metadata.name
                    try:
                        ns_quota_status = (
                            self.core.read_namespaced_resource_quota_status(
                                ns_quota_name, self.namespace
                            )
                        )
                        self.logger.debug(
                            "Fetched %s namespace resource quota %s status: %s",
                            self.namespace,
                            ns_quota_name,
                            ns_quota_status.status,
                        )
                    except ApiException as exp:
                        self.logger.warning(
                            "Exception when calling CoreV1Api>"
                            "read_namespaced_resource_quota_status: %s",
                            exp,
                        )

                    for key in ns_quota_status.status.hard:
                        quota_used = ns_quota_status.status.used[key]
                        quota_hard_limit = ns_quota_status.status.hard[key]
                        quota_type = key

                        ResourceQuotaWrench.quota_usage_status(
                            self,
                            quota_type,
                            ns_quota_name,
                            quota_used,
                            quota_hard_limit,
                        )
            else:
                self.logger.info(
                    "No resource quota found in namespace %s.",
                    self.namespace,
                )
        except ApiException as exp:
            self.logger.error(
                "Exception when calling CoreV1Api->read_namespaced_resource_quota: %s\n",
                exp,
            )
        return quota_chk_result
