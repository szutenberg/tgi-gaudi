import os
import time
import threading
from queue import Queue
from datetime import datetime

DBG_TRACE_QUEUE = Queue()
DBG_TRACE_FILENAME = os.environ.get('DBG_TRACE_FILENAME')
DBG_TRACE_THREAD = None


def dbg_trace_saver_thread():
    global DBG_TRACE_THREAD
    start_ts = None
    print('{"traceEvents": [', flush=True,
          file=open(DBG_TRACE_FILENAME+".json", 'w'))

    now = datetime.now()
    dt_string = now.strftime("%Y-%m-%d %H:%M:%S")
    print("TGI Logger started on {}".format(dt_string),
          flush=True, file=open(DBG_TRACE_FILENAME, 'w'))
    separator = ""
    last = None
    while True:
        e = DBG_TRACE_QUEUE.get()
        if start_ts is None:
            start_ts = e['time']
        e['time'] -= start_ts
        print("{:.3f} | {} | {}".format(e['time'], e['tag'], e['txt']), flush=True,
              file=open(DBG_TRACE_FILENAME, 'a'))
        if last:
            js = {"pid": 1, "tid": 1, "ph": "X",
                  "name": last['tag'],
                  "ts": last['time'] * 1e6,
                  "dur": (e['time'] - last['time']) * 1e6,
                  "args": last['txt']
                  }
            dur = str((e['time'] - last['time']) * 1e6)
            ts = str(last['time'] * 1e6)
            s = separator + '{"pid": 1, "tid": 2, "ph": "X", "name": "' + last['tag'] + '", "ts": ' + \
                ts + ', "dur": ' + dur + \
                ', "args": {"txt":"' + last['txt'] + '"}}'

            print(s, flush=True, file=open(DBG_TRACE_FILENAME+".json", 'a'))
            separator = ","
            if e['tag'] == "STOP":
                print("]}", flush=True, file=open(
                    DBG_TRACE_FILENAME+".json", 'a'))
                DBG_TRACE_THREAD = None
                break

        last = e


def dbg_trace(tag, txt):
    global DBG_TRACE_THREAD
    if DBG_TRACE_FILENAME is not None and int(os.getenv("RANK", 0)) == 0:
        if DBG_TRACE_THREAD is None:
            DBG_TRACE_THREAD = threading.Thread(target=dbg_trace_saver_thread)
            DBG_TRACE_THREAD.start()
        event = {"time": time.perf_counter(),
                 "tag": tag,
                 "txt": txt}
        DBG_TRACE_QUEUE.put(event)


if __name__ == "__main__":
    print("Test debug utils")
    event_names = ["GENERATE", "PREFILL", "CONCAT"]
    for i in range(12):
        tag = event_names[i % len(event_names)]
        print("dbg_trace({}, {})".format(tag, i))
        dbg_trace(tag, str(i))
        time.sleep(0.01 * i)
    DBG_TRACE_QUEUE.put(
        {"time": time.perf_counter(), "tag": "STOP", "txt": ""})
