from subprocess import Popen, PIPE


def execute(cmd: str, scharf: bool = False) -> None:
    print(f"{cmd}")
    if scharf:
        p = Popen(cmd, shell=True, stdout=PIPE, stderr=PIPE)
        p.wait()
        if p.returncode != 0:
            print(p.communicate())

