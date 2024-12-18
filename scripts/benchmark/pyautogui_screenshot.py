import threading
import time

import numpy as np
import psutil
import pyautogui

process = psutil.Process()
cpu_usage = []
mem_usage = []


def monitor_process_usage(stop_event, interval=0.1):
    while not stop_event.is_set():
        cpu = process.cpu_percent(interval=None)
        mem = process.memory_percent()
        cpu_usage.append(cpu)
        mem_usage.append(mem)
        time.sleep(interval)


stop_event = threading.Event()
monitor_thread = threading.Thread(target=monitor_process_usage, args=(stop_event,))
monitor_thread.start()

time_arr = []
for _ in range(300):
    start = time.time()
    img = pyautogui.screenshot()
    # img: PIL.Image.Image
    time_arr.append(time.time() - start)

stop_event.set()
monitor_thread.join()

mean_time = np.mean(time_arr) * 1000
std_time = np.std(time_arr) * 1000
mean_cpu = np.mean(cpu_usage)
mean_mem = np.mean(mem_usage)

print(f"PyAutoGUI screenshot()")
print(f"Elapsed time: {mean_time:.2f} ms ± {std_time:.2f} ms")
print(f"Mean CPU usage: {mean_cpu:.2f}%")
print(f"Mean memory usage: {mean_mem:.2f}%")

"""
Sample Results:

PyAutoGUI screenshot()
Elapsed time: 33.32 ms ± 1.79 ms
Mean CPU usage: 4.06%
Mean memory usage: 0.28%
"""
