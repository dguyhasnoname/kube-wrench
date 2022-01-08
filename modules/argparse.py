import argparse


class ArgParse:
    def arg_parse():
        p = argparse.ArgumentParser(
            description="""This script can be debug issues in a namespace in a Kubernetes cluster.

Before running script export KUBECONFIG file as env:
    export KUBECONFIG=<kubeconfig file location>

    e.g. export KUBECONFIG=/Users/dguyhasnoname/kubeconfig\n
ALternatively kubeconfig can be passed as argument.\n""",
            epilog="""All's well that ends well.""",
        )

        p.add_argument(
            "-k",
            "--kubeconfig",
            help="pass kubeconfig of the cluster. If not passed, picks KUBECONFIG from env",
        )
        p.add_argument(
            "-n", "--namespace", help="check resources in specific namespace."
        )
        p.add_argument(
            "-o",
            "--output",
            default="stdout",
            help="output formats csv|json|tree. Default is text on stdout.",
        )
        p.add_argument(
            "--dump",
            help="take dump of k8s objects. pass comma separated k8s objects."
            ' Pass "all" to take dumps for all supported objects.',
        )
        p.add_argument(
            "--loglevel", default="INFO", help="sets logging level. default is INFO"
        )
        p.add_argument("--silent", action="store_true", help="silence the logging.")

        args = p.parse_args()
        return args
