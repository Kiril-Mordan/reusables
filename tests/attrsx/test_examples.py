import logging

import attrs
from python_modules.attrsx import define
import pytest


# ---------------------------------------------------------------------------
# 1. Built-in logger
# ---------------------------------------------------------------------------

@define
class _ProcessData:
    data: str = attrs.field(default=None)

    def run(self):
        self.logger.info("Running data processing …")
        self.logger.debug("Processing data: %s", self.data)
        return f"Processed: {self.data}"


def test_logger_basic():
    obj = _ProcessData(data="x")
    # logger is created automatically
    assert obj.logger.name == _ProcessData.__name__
    assert obj.logger.level == logging.INFO
    assert obj.run() == "Processed: x"


def test_logger_custom_level():
    @define
    class _Verbose:
        data: str = attrs.field(default=None)
        loggerLvl: int = attrs.field(default=logging.DEBUG)

        def run(self):
            return self.logger.level

    assert _Verbose(data="x").run() == logging.DEBUG


def test_external_logger_is_used():
    ext = logging.getLogger("ext")
    ext.setLevel(logging.WARNING)
    obj = _ProcessData(data="x", logger=ext)
    assert obj.logger is ext
    assert obj.logger.level == logging.WARNING


# ---------------------------------------------------------------------------
# 2. Built-in handlers
# ---------------------------------------------------------------------------

class _Upper:
    def run(self, text: str) -> str:
        return text.upper()


@define(handler_specs={"proc": _Upper})
class _Service:
    initial : str = attrs.field()

    def run(self):
        self._initialize_proc_h()
        return self.proc_h.run(self.initial)


def test_handler_lazy_instantiation():
    s = _Service(initial="hi")
    # not built yet
    assert s.proc_h is None
    s._initialize_proc_h()
    assert isinstance(s.proc_h, _Upper)
    assert s.run() == "HI"


def test_handler_override_class_and_params():
    class _Reverse:
        def __init__(self, suffix=""):
            self.suffix = suffix

        def run(self, text):
            return text[::-1] + self.suffix

    svc = _Service(
        initial="abc",
        proc_class=_Reverse,
        proc_params={"suffix": "!"},
    )
    assert svc.run() == "cba!"


def test_handler_external_instance():
    ext = _Upper()
    svc = _Service(initial="abc", proc_h=ext)
    assert svc.proc_h is ext
    assert svc.run() == "ABC"


# ---------------------------------------------------------------------------
# 3. Logger chaining
# ---------------------------------------------------------------------------

@define(
    handler_specs={"proc": _ProcessData},
    logger_chaining={"logger": True},
)
class _Chained:
    loggerLvl = attrs.field(default=logging.DEBUG)

    def __attrs_post_init__(self):
        self._initialize_proc_h()

    def run(self):
        return self.proc_h.logger  # return handler’s logger for assertion


def test_logger_chaining_identity():
    parent = _Chained()
    assert parent.run() is parent.logger


# ---------------------------------------------------------------------------
# 4. Injection is always on
# ---------------------------------------------------------------------------

def test_define_always_injects_logger_fields():
    @define
    class Dummy:
        x: int = attrs.field()

    field_names = {f.name for f in attrs.fields(Dummy)}
    expected = {"x", "logger", "loggerLvl", "logger_name", "logger_format"}
    assert expected.issubset(field_names)