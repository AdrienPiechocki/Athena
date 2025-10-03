import os
import importlib
import inspect

__all__ = []

# Current folder
folder = os.path.dirname(__file__)

# stocks every function dynamicly
functions_registry = {}

for filename in os.listdir(folder):
    if filename.endswith(".py") and filename != "__init__.py":
        module_name = filename[:-3]
        module = importlib.import_module(f".{module_name}", package=__name__)
        
        for name, obj in inspect.getmembers(module):
            if inspect.isfunction(obj):
                functions_registry[name] = obj
                globals()[name] = obj
                __all__.append(name)
