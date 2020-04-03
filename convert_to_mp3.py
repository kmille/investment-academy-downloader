#!/usr/bin/env python3
from util import execute
from shlex import quote
from multiprocessing import Process
import os
import sys

convert_cmd = "ffmpeg -y -loglevel warning -i {} -b:a 320k {}"
dir_mp3 = "mp3"


def mp3_to_mp4(dir_in: str) -> None:
    if not os.path.exists(dir_in):
        print(f"Dir '{dir_in}' does not exist")
        return
    dir_out = os.path.join(dir_in, dir_mp3)

    os.makedirs(dir_out, exist_ok=True)

    process_list = []
    for mp4 in os.listdir(dir_in):
        print(f"Converting '{mp4}' to mp3")
        file_in = os.path.join(dir_in, mp4)
        file_name = "".join(mp4.split(".")[:-1]) + ".mp3"
        file_out = os.path.join(dir_out, file_name)
        if os.path.exists(file_out):
            print(f"File '{file_out}' already exists")
            continue
        cmd = convert_cmd.format(quote(file_in), quote(file_out))
        p = Process(target=execute, args=(cmd, True))
        p.start()
        process_list.append(p)
    print("Started all processes")
    for p in process_list:
        p.join()


if __name__ == '__main__':
    if len(sys.argv) == 1:
        print(f"{sys.argv[0]} <dir of mp4 files to convert>")
        sys.exit(1)
    dir_in = sys.argv[1]
    mp3_to_mp4(dir_in)
