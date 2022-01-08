import os, sys, time, urllib3
start_time = time.time()
from modules.logging import Logger
from modules.argparse import ArgParse
from modules.kube_config import KubeConfig
from modules.resource_quota import ResourceQuotaWrench
from modules.pods import PodWrench
from modules.output import Output

class KubeWrench():
    def __init__(self, logger, k8s_config, namespace):
        self.logger = logger
        self.k8s_config = k8s_config
        self.namespace = namespace

    def kube_wrench(self):
        self.logger.info("Starting kube-wrench.")
        ResourceQuotaWrench(self.k8s_config, self.namespace, self.logger).resource_quota_wrench()
        PodWrench(self.k8s_config, self.namespace, self.logger).pod_wrench()

def main():
    urllib3.disable_warnings()
    args = ArgParse.arg_parse()
    logger = Logger.get_logger(args.output, args.silent, args.loglevel)
    k8s_config = KubeConfig.load_kube_config(args.output, logger)
    namespace = args.namespace
    call = KubeWrench(logger, k8s_config, namespace)
    call.kube_wrench()
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
