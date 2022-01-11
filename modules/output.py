"""[Output module for kube-wrench]
"""
import time

class Output:
    """[Output class for kube-wrench]"""
    RED = "\033[41m"
    ORANGE = "\033[91m"
    GREEN = "\033[32m"
    YELLOW = "\033[43m"
    LIGHTYELL = "\033[33m"
    RESET = "\033[0m"
    BOLD = "\033[1;30m"
    MARKER = "\u2309\u169B\u22B8"
    FALSE = RED + "False" + RESET
    TRUE = GREEN + "True" + RESET

    def time_taken(start_time):
        """[Calculate time taken]"""
        print(
            Output.GREEN
            + "\nTotal time taken: "
            + Output.RESET
            + "{}s".format(round((time.time() - start_time), 2))
        )


    def convert_cpu(cpu_val):
        """[Convert to cpu cores]

        Args:
            cpu_val ([str/int]): [Cpu value]

        Returns:
            [int]: [Cpu cores]
        """
        cpu_str = str(cpu_val)
        if cpu_str == "":
            cpu = 0
        elif "m" in cpu_str:
            cpu = int(cpu_str.replace("m", "")) / 1000
        else:
            cpu = int(cpu_str)
        return cpu

    def convert_memory(memory_val):
        """[Convert to memory in GB]

        Args:
            memory_val ([str/int]): [Memory value]

        Returns:
            [int]: [Memory in GB]
        """
        memory_str = str(memory_val)
        if memory_str == "":
            memory = 0
        elif "Mi" in memory_str:
            memory = int(memory_str.replace("Mi", "")) / 1000
        elif "Ki" in memory_str:
            memory = int(memory_str.replace("Ki", "")) / 1000000
        else:
            memory = int(memory_str.replace("Gi", ""))
        return memory
