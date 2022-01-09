"""[Module to process ingress details]"""
import kubernetes.client
from kubernetes.client.rest import ApiException
import requests
import requests.exceptions


class IngressWrench:
    """[Class to determine ingress status]"""

    def __init__(self, k8s_config, namespace, logger):
        self.k8s_config = k8s_config
        self.namespace = namespace
        self.logger = logger
        with kubernetes.client.ApiClient(k8s_config) as api_client:
            self.network = kubernetes.client.NetworkingV1Api(api_client)

        self.logger.debug("Fetching %s namespace ingress data.", self.namespace)
        try:
            self.ingress = self.network.list_namespaced_ingress(
                self.namespace, timeout_seconds=10
            )
        except ApiException as exp:
            self.logger.warning(
                "Exception when calling NetworkingV1Api->list_namespaced_ingress: %s",
                exp,
            )

    def ingress_wrench(self, svc):
        ing_mapped_to_svc = ""
        self.logger.debug(
            "Analyzing ingress mapped to service %s/%s.",
            self.namespace,
            svc.metadata.name,
        )
        for ing in self.ingress.items:
            try:
                for rule in ing.spec.rules:
                    for path in rule.http.paths:
                        if path.backend.service.name in svc.metadata.name:
                            ing_mapped_to_svc = ing.metadata.name
                            self.logger.info(
                                "Ingress %s is mapped to service %s/%s. Host/Path: %s%s. Path type: %s.",
                                ing_mapped_to_svc,
                                self.namespace,
                                svc.metadata.name,
                                rule.host,
                                path.path,
                                path.path_type,
                            )
                            try:
                                response = requests.get(
                                    "http://{}{}".format(rule.host, path.path),
                                    timeout=5,
                                )
                                status_code = status_code
                            except requests.exceptions.Timeout:
                                self.logger.warning(
                                    "Timeout exception when calling http://{}{}.".format(
                                        rule.host, path.path
                                    )
                                )
                                status_code = "408"
                            except requests.exceptions.TooManyRedirects:
                                self.logger.warning(
                                    "Too many redirects when calling http://{}{}.".format(
                                        rule.host, path.path
                                    )
                                )
                                status_code = ""

                            if status_code == 200:
                                self.logger.info(
                                    "Service %s/%s mapped with ingress %s working. Response code: %s",
                                    self.namespace,
                                    svc.metadata.name,
                                    ing_mapped_to_svc,
                                    status_code
                                )
                            elif status_code == 302:
                                self.logger.info(
                                    "Service %s/%s mapped with ingress %s seems to responding. Response code: %s",
                                    self.namespace,
                                    svc.metadata.name,
                                    ing_mapped_to_svc,
                                    status_code
                                )
                            elif status_code in [400, 404, 500, 501, 502, 503, 504]:
                                self.logger.warning(
                                    "Service %s/%s mapped with ingress %s is not working. Response code: %s",
                                    self.namespace,
                                    svc.metadata.name,
                                    ing_mapped_to_svc,
                                    status_code
                                )
                            else:
                                self.logger.warning(
                                    "Service %s/%s mapped with ingress %s needs to checked. Response code: %s",
                                    self.namespace,
                                    svc.metadata.name,
                                    ing_mapped_to_svc,
                                    status_code
                                )
                            break
            except AttributeError:
                self.logger.debug("No rules found in ingress %s.", ing.metadata.name)
        if not ing_mapped_to_svc:
            self.logger.info(
                "No Ingress mapping found for service %s/%s.",
                self.namespace,
                svc.metadata.name,
            )
        return ing_mapped_to_svc
