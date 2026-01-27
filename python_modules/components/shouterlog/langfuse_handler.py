"""
Includes simple handler for Langfuse to leave traces with shouterlog.
"""

import hashlib
import os
import uuid
from collections.abc import Callable
from enum import Enum
from typing import Any, Dict, List, Optional, Type, get_type_hints

import attrs
import attrsx
from pydantic import BaseModel, Field, SkipValidation

#! langfuse >= 3.11.2

__design_choices__ = {
    'trace_grouping' : ['trace_id is derived from session_id and root frame to keep related spans grouped',
                        'root frame is the first element of the resolved traceback path',
                        'changing session_id or root frame creates a new trace group'],
    'traceback_handling' : ['tracebacks may be leaf->root or root->leaf; handler normalizes when possible',
                            'missing or malformed tracebacks fall back to a flat span'],
    'executed_funcs' : ['executed_funcs accumulates unique functions per trace_id across calls',
                        'executed_funcs is attached to every span metadata for filterability',
                        'executed_funcs_count provides a compact numeric filter for quick queries'],
    'tags' : ['tags are always coerced to a list and appended with fn:<function> when available',
              'tags are kept lightweight to avoid high-cardinality metadata'],
    'levels' : ['log levels are mapped to Langfuse logging levels for consistent severity filters']
}

class LangfuseLoggingLevel(Enum):
    """Log levels mapped to Langfuse logging levels."""
    DEFAULT = "DEFAULT"
    DEBUG = "DEBUG"
    WARNING = "WARNING"
    ERROR = "ERROR"


class LogTraceInput(BaseModel):

    """
    Acceptable log trace inputs
    """

    session_id: str = Field(description = "Session id")
    trace_name: Optional[str] = Field(default = None, description = "Trace name")
    level: Optional[LangfuseLoggingLevel] = Field(default = LangfuseLoggingLevel.DEFAULT, description = "Logging level")
    input: Optional[Any] = Field(default = None, description = "Optional input") 
    output: Optional[Any] = Field(default = None, description = "Optional output") 
    metadata: Optional[Dict[str, Any]] = Field(default = None, description = "Optional metadata") 
    user_id: Optional[str] = Field(default = None, description = "Optional user id")
    tags: Optional[list[str]] = Field(default = None, description = "Optional list of tags") 
    
    model_config = {
        "arbitrary_types_allowed": True
    }


@attrsx.define()
class LangfuseHandler:
    """Handler that converts Shouter log records into Langfuse spans."""

    input_model = attrs.field(default = LogTraceInput)
    langfuse = attrs.field(default = None)
    propagate_attributes = attrs.field(default = None)
    session_id : str = attrs.field(default = None)
    _span_by_path : dict = attrs.field(default = None)
    _executed_funcs_by_trace : dict = attrs.field(default = None)


    env_mapping : dict = attrs.field(factory=dict)
    params: dict = attrs.field(factory=dict)

    def __attrs_post_init__(self):

        self.set_session_id()
        self._initialize_langfuse()
        self.input_model = LogTraceInput
        if self._executed_funcs_by_trace is None:
            self._executed_funcs_by_trace = {}

    def _initialize_langfuse(self):

        try:
            from langfuse import Langfuse, propagate_attributes
        except ImportError as e:
            raise ImportError("Failed to import Langfuse!") from e


        input_params = {k : os.getenv(v) for k,v in self.env_mapping.items()}
        if self.params:
            input_params.update(self.params)


        if self.langfuse is None:
            self.langfuse = Langfuse(
                **input_params)

        if self.propagate_attributes is None:
            self.propagate_attributes = propagate_attributes

        
    def set_session_id(self):
        """Generate a new session id for grouping traces."""

        self.session_id = uuid.uuid4().hex

    def _to_hex32(self, s: str) -> str:
        return hashlib.sha256(s.encode("utf-8")).hexdigest()[:32]

    def _update_executed_funcs(self, trace_id: str, tb: list[str]) -> dict:
        acc = self._executed_funcs_by_trace.setdefault(trace_id, set())
        acc.update(tb or [])
        return {
            "executed_funcs": sorted(acc),
            "executed_funcs_count": len(acc),
        }

    def _prepare_inputs(
        self, 
        params : dict,
        log_item : dict = None):

        if log_item is None:
            log_item = {}
        
        lvl = (log_item.get("level") or "").lower()
        level_map = {
            "info": "DEFAULT",
            "debug": "DEBUG",
            "warning": "WARNING",
            "error": "ERROR",
            "fatal": "ERROR",
            "critical": "ERROR",
        }
        params["level"] = level_map.get(lvl, params.get("level") or "DEFAULT")

        if params.get("session_id") is None:
            params["session_id"] = self.session_id

        if params.get("metadata") is None:
            params["metadata"] = {}

        metadata = params["metadata"]

        # --- compute traceback + depth ---
        tb = log_item.get("traceback")
        # allow tb to be list/tuple; ignore other types safely
        if isinstance(tb, (list, tuple)):
            depth = max(len(tb) - 1, 0)
            metadata["traceback"] = list(tb)
            metadata["depth"] = int(depth)
            metadata["leaf_function"] = tb[0] if tb else None
            metadata["root_function"] = tb[-1] if tb else None
        else:
            depth = None  # unknown / not provided

        if log_item.get("idx"):
            metadata["call_idx"] = log_item["idx"]

        if log_item.get("datetime"):
            metadata["datetime"] = log_item["datetime"]
        
        if log_item.get("level"):
            metadata["level"] = log_item["level"]
        
        if log_item.get("mess"):
            metadata["mess"] = log_item["mess"]

        if log_item.get("call_id"):
            metadata["call_id"] = log_item["call_id"]

        if log_item.get("function"):
            metadata["function"] = log_item["function"]

        if log_item.get("traceback"):
            metadata["traceback"] = log_item["traceback"]

        metadata["session_id"] = params["session_id"]

        # --- choose a span name that is useful without trace_name ---
        base_name = (
            log_item.get("function")
            or log_item.get("label")
            or (str(log_item["idx"]) if log_item.get("idx") is not None else None)
            or "log"
        )

        params["trace_name"] = base_name

        # --- tags: ensure list, append depth/function tags ---
        tags = params.get("tags") or []
        if not isinstance(tags, list):
            tags = [str(tags)]

        if log_item.get("function"):
            tags.append(f"fn:{log_item['function']}")


        params["tags"] = tags

        return self.input_model(
            **params
        )


    def log_trace(self, 
        session_id: Optional[str] = None,
        trace_name: Optional[str] = None,
        level: Optional[LangfuseLoggingLevel] = None,
        input: Optional[Any] = None,
        output: Optional[Any] = None,
        metadata: Optional[Dict[str, Any]] = None,
        user_id: Optional[str] = None,
        tags: Optional[list[str]] = None
        ) -> None:
        """Create Langfuse spans for a log record, including nested tracebacks."""

        if session_id is None:
            session_id = self.session_id

        if level is None:
            level = LangfuseLoggingLevel.DEFAULT
        
        if metadata is None:
            metadata = {}

        tb = (metadata.get("traceback") or [])
        if not isinstance(tb, (list, tuple)) or not tb:
            # No traceback => just log a flat span grouped by session
            trace_id = self._to_hex32(str(session_id))
            with self.propagate_attributes(
                session_id=session_id,
                user_id=user_id,
                tags=tags,
            ):
                with self.langfuse.start_as_current_observation(
                    as_type="span",
                    trace_context={"trace_id": trace_id},
                    name=trace_name,
                    input=input,
                    output=output,
                    metadata=metadata,
                    level=level.value,
                ):
                    pass
            return

        # Prefer to only reverse if we are confident the order is leaf->root
        path = list(tb)
        leaf_fn = metadata.get("function")
        if leaf_fn and tb:
            if tb[0] == leaf_fn:
                # tb is leaf->root -> reverse to root->leaf
                path = list(reversed(tb))
            elif tb[-1] == leaf_fn:
                # tb is root->leaf -> keep as-is
                path = list(tb)
        root_frame = path[0]

        # ---- trace grouping: (session_id + root_frame) ----
        # This prevents linking between sessions and between unrelated roots.
        trace_key = f"{session_id}|{root_frame}"
        trace_id = self._to_hex32(trace_key)
        exec_meta = self._update_executed_funcs(trace_id, list(tb))

        # ---- init prefix map store ----
        # Maps a path prefix tuple to a REAL Langfuse span id (16-hex).
        if not hasattr(self, "_span_by_path") or self._span_by_path is None:
            self._span_by_path = {}

        with self.propagate_attributes(
            session_id=session_id,
            user_id=user_id,
            tags=tags,
        ):
            parent_span_id = None

            # Ensure all prefix nodes exist as nested spans.
            # This is what makes Langfuse "L depth" reflect your traceback depth.
            for i, frame in enumerate(path):
                prefix = tuple(path[: i + 1])

                # Already created this prefix in this session/root trace -> reuse it as parent
                span_id = self._span_by_path.get((trace_id, prefix))
                if span_id:
                    parent_span_id = span_id
                    continue

                # Create a span for this frame/prefix
                with self.langfuse.start_as_current_observation(
                    as_type="span",
                    trace_context={
                        "trace_id": trace_id,
                        **({"parent_span_id": parent_span_id} if parent_span_id else {}),
                    },
                    name=frame,
                    metadata={
                        # keep your useful fields, but don't spam prompt/response on every frame
                        "frame": frame,
                        "depth": int(i),
                        "root": root_frame,
                        "leaf": path[-1],
                        "traceback": list(tb),  # keep original leaf->root too
                        "call_id": metadata.get("call_id"),
                        **exec_meta,
                    },
                    level=level.value,
                ) as span:
                    sid = getattr(span, "id", None)
                    if isinstance(sid, str) and len(sid) == 16:
                        self._span_by_path[(trace_id, prefix)] = sid
                        parent_span_id = sid
                    else:
                        # If we can't get a valid span id, stop trying to nest further.
                        parent_span_id = None
                        break

            # Finally, attach the actual log event under the leaf frame span (if any)
            # This keeps “frame spans” clean and puts the real payload at the leaf.
                with self.langfuse.start_as_current_observation(
                    as_type="span",
                    trace_context={
                        "trace_id": trace_id,
                        **({"parent_span_id": parent_span_id} if parent_span_id else {}),
                    },
                    name=trace_name,
                    input=input,
                    output=output,
                    metadata={**metadata, **exec_meta},
                    level=level.value,
                ):
                    pass


    def flush(self):
        """Flush pending Langfuse spans."""
        self.langfuse.flush()
