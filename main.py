import os
import sys
import ctypes
import multiprocessing as mp

from rggbar import qt
from rggbar import web


def main():
    if os.name == 'nt':
        kernel32 = ctypes.WinDLL('kernel32', use_last_error=True)
        process_array = (ctypes.c_uint8 * 1)()
        num_processes = kernel32.GetConsoleProcessList(process_array, 1)
        if num_processes < 3:
            ctypes.WinDLL('user32').ShowWindow(kernel32.GetConsoleWindow(), 0)

        mp.freeze_support()



    if getattr(sys, 'frozen', False):
        work_dir = sys._MEIPASS
    else:
        work_dir = os.path.dirname(os.path.abspath(__file__))

    p = mp.Process(target=web.run, args=(work_dir,))
    p.start()

    qt.start(work_dir)

    p.terminate()


if __name__ == "__main__":
    main()