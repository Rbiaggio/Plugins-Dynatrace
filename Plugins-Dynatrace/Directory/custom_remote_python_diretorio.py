import sys
import time
import logging
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

class MyHandler(FileSystemEventHandler):
    def on_any_event(self, event):
        print ('Evento', event.event_type,' caminho:', event.src_path, 'diretorio?', event.is_directory)


path = 'C:\/Users\/rodri\/OneDrive\/Documents\/Monit'
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S')
observer = Observer()
observer.schedule(MyHandler(), path, recursive=True)
observer.start()
try:
    while True:
        time.sleep(2000)
except KeyboardInterrupt:
    observer.stop()
observer.join()

