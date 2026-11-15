import multiprocessing
import warnings

from RestrictedPython import compile_restricted, safe_globals
from RestrictedPython.Guards import guarded_iter_unpack_sequence
from RestrictedPython.PrintCollector import PrintCollector

ctx = multiprocessing.get_context("fork")


def _worker(code_str, conn):
    try:
        with warnings.catch_warnings():
            warnings.filterwarnings(
                "ignore", message=".*Prints, but never reads 'printed' variable.*"
            )
            byte_code = compile_restricted(code_str, filename="<string>", mode="exec")

        env = safe_globals.copy()
        env["_print_"] = PrintCollector
        env["_getattr_"] = getattr
        env["_getiter_"] = iter
        env["_iter_unpack_sequence_"] = guarded_iter_unpack_sequence

        env["sum"] = sum
        env["min"] = min
        env["max"] = max
        env["len"] = len
        env["range"] = range

        exec(byte_code, env)  # noqa: S102

        output = env["_print"]() if "_print" in env else ""
        result = env.get("result", None)
        conn.send({"status": "ok", "output": output, "result": result})

    except Exception as e:  # noqa: BLE001
        conn.send({"status": "error", "message": str(e)})
    finally:
        conn.close()


def run_code(code_str, timeout=4.0):
    parent_conn, child_conn = ctx.Pipe(duplex=False)
    prozess = ctx.Process(target=_worker, args=(code_str, child_conn))

    prozess.start()
    child_conn.close()

    prozess.join(timeout)

    if prozess.is_alive():
        prozess.terminate()
        prozess.join()
        parent_conn.close()
        return {"status": "timeout", "message": "Zeitlimit überschritten!"}

    if parent_conn.poll():
        ergebnis = parent_conn.recv()
        parent_conn.close()
        return ergebnis

    parent_conn.close()
    return {"status": "error", "message": "Prozess ohne Ergebnis beendet"}
