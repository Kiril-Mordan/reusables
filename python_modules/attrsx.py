"""
**`attrsx` – A Lightweight, Playful Extension to `attrs`**  

🔧 **What is `attrsx`?**  
`attrsx` is a minimal, lightweight extension of the popular `attrs` library, designed to seamlessly add logging capabilities to your `attrs` classes.  

---

### **✨ What It Does:**  
- 🛠️ **Extends `attrs.define`** – Behaves exactly like `attrs.define`, but with automatic logger initialization.  
- 🎛️ **Built-in Logging Fields** – Adds fields for logger name, level, and format – all customizable per class or instance.  
- 🔍 **Non-Intrusive** – If you don’t need logging, `attrsx` functions just like plain old `attrs`.  

---

### **🎯 Why `attrsx`?**  
- 🚀 You sometimes just want **simple logging** without writing the same boilerplate over and over.  
- 😌 `attrsx` lets you keep things clean – adding just a little "magic" to `attrs`-based classes.  
- 🌱 It’s `attrs`, but with room for playful future extensions.  

---

### **🚧 Features at a Glance:**  
- ✅ **Fully compatible** with `attrs` 22.2.0 and later.  
- 🧩 Supports **all `attrs.define` parameters** – like `slots`, `frozen`, and more.  
- 🔧 Logger defaults to the class name but can be **overridden effortlessly**.  

---

✨ It’s `attrs`, but with just a little... **extra**. 😄  
"""

import attrs #>=22.2.0
import logging


__package_metadata__ = {
    "author": "Kyrylo Mordan",
    "author_email": "parachute.repo@gmail.com",
    "description": "A lightweight extension of attrs that adds extras like logging.",
    'license' : 'mit',
    "url" : 'https://kiril-mordan.github.io/reusables/attrsx/'
}

def define(cls=None, *args, **kwargs):
    if cls is not None:
        return _apply_attrs_and_logger(cls, *args, **kwargs)
    
    def wrapper(inner_cls):
        return _apply_attrs_and_logger(inner_cls, *args, **kwargs)
    
    return wrapper


def _apply_attrs_and_logger(cls, *args, **kwargs):
    # Inject logger fields ONLY if they don't already exist
    if 'logger' not in cls.__dict__:
        cls.logger = attrs.field(default = None, repr=False)
    if 'loggerLvl' not in cls.__dict__:
        cls.loggerLvl = attrs.field(default=logging.INFO)
    if 'logger_name' not in cls.__dict__:
        cls.logger_name = attrs.field(default=None)
    if 'logger_format' not in cls.__dict__:
        cls.logger_format = attrs.field(default="%(levelname)s:%(name)s:%(message)s")

    # Preserve existing __attrs_post_init__ if it exists
    original_post_init = getattr(cls, "__attrs_post_init__", None)

    # Define a wrapper __attrs_post_init__ to initialize the logger
    def __attrs_post_init__(self):
        # Logger setup (before custom post-init logic)
        if not hasattr(self, 'logger') or self.logger is None:
            self.logger = logging.getLogger(self.logger_name or self.__class__.__name__)
            self.logger.setLevel(self.loggerLvl)

            # Clear existing handlers to avoid duplicates
            self.logger.handlers.clear()

            handler = logging.StreamHandler()
            formatter = logging.Formatter(self.logger_format)
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            self.logger.propagate = False  # Prevent log duplication

        # Call the original post-init if it exists
        if original_post_init:
            original_post_init(self)

    # Attach the wrapped __attrs_post_init__ to the class
    cls.__attrs_post_init__ = __attrs_post_init__

    # Apply attrs.define
    return attrs.define(cls, *args, **kwargs)

