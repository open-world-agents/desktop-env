import threading
import time

import numpy as np
import psutil
from PIL import ImageGrab

# Get the current process
process = psutil.Process()

# Lists to store CPU and memory usage samples
cpu_usage = []
mem_usage = []


# Function to monitor CPU and memory usage
def monitor_process_usage(stop_event, interval=0.1):
    while not stop_event.is_set():
        cpu = process.cpu_percent(interval=None)
        mem = process.memory_percent()
        cpu_usage.append(cpu)
        mem_usage.append(mem)
        time.sleep(interval)


# Start monitoring thread
stop_event = threading.Event()
monitor_thread = threading.Thread(target=monitor_process_usage, args=(stop_event,))
monitor_thread.start()

# Benchmarking code
time_arr = []
for _ in range(300):  # 30 FPS * 10 seconds
    start = time.time()
    img = ImageGrab.grab()
    # img: PIL.Image.Image
    time_arr.append(time.time() - start)

# Stop monitoring thread
stop_event.set()
monitor_thread.join()

# Calculate results
mean_time = np.mean(time_arr) * 1000
std_time = np.std(time_arr) * 1000
mean_cpu = np.mean(cpu_usage)
mean_mem = np.mean(mem_usage)

print(f"PIL ImageGrab.grab()")
print(f"Elapsed time: {mean_time:.2f} ms ± {std_time:.2f} ms")
print(f"Mean CPU usage: {mean_cpu:.2f}%")
print(f"Mean memory usage: {mean_mem:.2f}%")

"""
Sample Results:

PIL ImageGrab.grab()
Elapsed time: 33.37 ms ± 2.12 ms
Mean CPU usage: 6.13%
Mean memory usage: 0.23%
"""
