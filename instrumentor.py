# Referenced the code of https://github.com/TheCherno/Hazel/blob/1feb70572fa87fa1c4ba784a2cfeada5b4a500db/Hazel/src/Hazel/Debug/Instrumentor.h

import threading
import time
import json


PROFILE = True


class ProfileResult:
    def __init__(self, name, start, elapsed_time, thread_id):
        self.name = name
        self.start = start
        self.elapsed_time = elapsed_time
        self.thread_id = thread_id


class InstrumentationSession:
    def __init__(self, name):
        self.Name = name


class Instrumentor:

    _instance = None

    def __init__(self):
        self.__mutex = threading.Lock()
        self.__current_session = None
        self.__output_stream = None

    def __del__(self):
        self.end_session()

    def begin_session(self, name, filepath="results.json"):
        if self.__current_session:
            print(
                f"Instrumentor.begin_session('{name}') when session '{self.__current_session.Name}' already open."
            )
            self.internal_end_session()

        self.__output_stream = open(filepath, "w")
        if self.__output_stream:
            self.__current_session = InstrumentationSession(name)
            self.write_header()
        else:
            print(f"Instrumentor could not open results file '{filepath}'.")

    def end_session(self):
        self.internal_end_session()

    def write_profile(self, args):
        result = ProfileResult(*args)
        json_data = {
            "cat": "function",
            "dur": str(result.elapsed_time),
            "name": str(result.name),
            "ph": "X",
            "pid": 0,
            "tid": str(result.thread_id),
            "ts": str(result.start),
        }

        with self.__mutex:
            if self.__current_session and self.__output_stream:
                self.__output_stream.write(", " + json.dumps(json_data))
                self.__output_stream.flush()

    @staticmethod
    def get():
        if not Instrumentor._instance:
            Instrumentor._instance = Instrumentor()
        return Instrumentor._instance

    def internal_end_session(self):
        if self.__current_session:
            self.write_footer()
            self.__output_stream.close()
            self.__current_session = None

    def write_header(self):
        with self.__mutex:
            if self.__output_stream:
                self.__output_stream.write('{"otherData": {},"traceEvents":[{}')
                self.__output_stream.flush()

    def write_footer(self):
        with self.__mutex:
            if self.__output_stream:
                self.__output_stream.write("]}")
                self.__output_stream.flush()


class InstrumentationTimer:
    def __init__(self, name: str) -> None:
        self.__name = name

    def __enter__(self) -> "InstrumentationTimer":
        if PROFILE:
            self.__start_time_point = int(time.perf_counter() * 1000000)  # us
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        if PROFILE:
            elapsed_time_count = (
                int(time.perf_counter() * 1000000) - self.__start_time_point
            )
            Instrumentor.get().write_profile(
                (
                    self.__name,
                    self.__start_time_point,
                    elapsed_time_count,
                    threading.get_ident(),
                )
            )
        pass


class InstrumentorUtils:
    @staticmethod
    def cleanup_output_string(expr: str, remove: str) -> str:
        result = []
        src_index = 0

        while src_index < len(expr):
            match_index = 0

            while (
                match_index < len(remove) - 1
                and src_index + match_index < len(expr) - 1
                and expr[src_index + match_index] == remove[match_index]
            ):
                match_index += 1

            if match_index == len(remove) - 1:
                src_index += match_index

            result.append("'" if expr[src_index] == '"' else expr[src_index])
            src_index += 1

        return "".join(result)


def PROFILE_SCOPE(name):
    return InstrumentationTimer(name=name)


def PROFILE_FUNCTION(func):
    def wrapper(*args, **kwargs):
        with PROFILE_SCOPE(name=str(func)):
            rtn = func(*args, **kwargs)
            return rtn

    return wrapper if PROFILE else func


def PROFILE_BEGIN_SESSION(name, filepath):
    if PROFILE:
        return Instrumentor.get().begin_session(name, filepath)


def PROFILE_END_SESSION():
    if PROFILE:
        return Instrumentor.get().end_session()
