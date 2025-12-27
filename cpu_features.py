import platform
import subprocess
import sys

def get_cpu_flags():
    flags = set()

    try:
        if platform.system() == "Linux":
            with open("/proc/cpuinfo", "r") as f:
                for line in f:
                    if line.lower().startswith("flags"):
                        flags.update(line.strip().split(":")[1].split())
                        break

        elif platform.system() == "Windows":
            # WMIC works even on stripped Windows builds
            out = subprocess.check_output(
                ["wmic", "cpu", "get", "Name,Architecture"],
                stderr=subprocess.DEVNULL,
                stdin=subprocess.DEVNULL,
                text=True
            )
            # Windows does NOT expose flags directly; assume worst-case
            # If user is on Atom / C-series / legacy netbook → legacy mode
            flags.add("windows_generic")

    except Exception:
        pass

    return flags


def is_legacy_cpu():
    flags = get_cpu_flags()

    # Anything without guaranteed SSE4.2 is legacy for us
    if "sse4_2" not in flags:
        return True

    # Defensive: older AMD chips misreport partial flags
    if "sse4a" in flags and "sse4_2" not in flags:
        return True

    # Windows generic fallback → assume legacy
    if "windows_generic" in flags:
        return True

    return False
