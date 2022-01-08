from packaging import version
import os, re, time, json, csv, math
from tabulate import tabulate


class Output:
    RED = "\033[41m"
    ORANGE = "\033[91m"
    GREEN = "\033[32m"
    YELLOW = "\033[43m"
    LIGHTYELL = "\033[33m"
    RESET = "\033[0m"
    BOLD = "\033[1;30m"
    MARKER = u"\u2309\u169B\u22B8"
    FALSE = RED + "False" + RESET
    TRUE = GREEN + "True" + RESET

    def time_taken(start_time):
        print(
            Output.GREEN
            + "\nTotal time taken: "
            + Output.RESET
            + "{}s".format(round((time.time() - start_time), 2))
        )

    # prints separator line between output
    def separator(color, char, l):
        if l:
            return
        columns, rows = os.get_terminal_size(0)
        for i in range(columns):
            print(color + char, end="" + Output.RESET)
        print("\n")

    def convert_cpu(cpu):
        if cpu == "":
            cpu = 0
        if "m" in cpu:
            cpu = math.ceil(float(cpu.replace("m", "")) / 1000)
        return int(cpu)

    def convert_memory(mem):
        if mem == "":
            memory = 0
        elif "Mi" in mem:
            memory = math.ceil(float(mem.replace("Mi", "")) / 1000)
        elif "Ki" in mem:
            memory = math.ceil(float(mem.replace("Ki", "")) / 1000000)
        else:
            memory = mem.replace("Gi", "")
        return int(memory)

