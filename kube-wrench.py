import os, sys, time, urllib3
start_time = time.time()
from modules.logging import Logger
from modules.argparse import ArgParse
from modules.kube_config import KubeConfig
from modules.resource_quota import ResourceQuotaWrench
from modules.pods import PodWrench
from modules.namespace import NameSpaceWrench
from modules.output import Output

class KubeWrench():
    def __init__(self, logger, k8s_config, namespace):
        self.logger = logger
        self.k8s_config = k8s_config
        self.namespace = namespace

    def kube_wrench_process(self):
            PodWrench(self.k8s_config, self.namespace, self.logger).pod_wrench()
            ResourceQuotaWrench(self.k8s_config, self.namespace, self.logger).resource_quota_wrench()
            NameSpaceWrench(self.k8s_config, self.logger).get_ns_events(self.namespace)

    def kube_wrench_main(self):
        self.logger.info("Starting kube-wrench.")
        if not self.namespace:
            self.logger.info("No namespace specified. Kube-wrench will run on default namespace.")
            self.namespace = "default"
            self.kube_wrench_process()
        elif self.namespace in ["all", "ALL", "All"]:
            self.logger.info("Running on all namespaces.")
            ns_list = NameSpaceWrench(self.k8s_config, self.logger).namespace_wrench()
            if ns_list:
                for ns in ns_list.items:
                    self.namespace = ns.metadata.name
                    self.kube_wrench_process()
                    print("\n\n")
        else:
            self.logger.info("Running on namespace: %s", self.namespace)
            self.kube_wrench_process()


def main():
    urllib3.disable_warnings()
    args = ArgParse.arg_parse()
    logger = Logger.get_logger(args.output, args.silent, args.loglevel)
    k8s_config = KubeConfig.load_kube_config(args.output, logger)
    namespace = args.namespace
    KubeWrench(logger, k8s_config, namespace).kube_wrench_main()
    Output.time_taken(start_time)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("[ERROR] Interrupted from keyboard!")
        try:
            sys.exit(0)
        except SystemExit:
            os._exit(0)
