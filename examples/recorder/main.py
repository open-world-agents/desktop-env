import time

from loguru import logger
from tqdm import tqdm

from desktop_env import Desktop, DesktopArgs

# how to use loguru with tqdm: https://github.com/Delgan/loguru/issues/135
logger.remove()
logger.add(lambda msg: tqdm.write(msg, end=""), colorize=True)

logger.enable("desktop_env")  # it's optional to enable the logger; just for debugging


if __name__ == "__main__":
    args = DesktopArgs(
        submodules=[{"module": "desktop_env.recorder.Recorder", "args": dict(filesink_location="output.mkv")}]
    )
    desktop = Desktop.from_args(args)

    try:
        # Option 1. Start the pipeline in the current thread (blocking)
        # desktop.start()

        # Option 2. Start the pipeline in a separate thread (non-blocking)
        desktop.start_free_threaded()
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        pass
    finally:
        desktop.stop()
        desktop.join()
        desktop.close()

        # or you may use desktop.stop_join_close()
