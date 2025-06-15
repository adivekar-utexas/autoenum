import re
import threading
import warnings
from enum import Enum, auto
from functools import lru_cache
from typing import (
    Any,
    Dict,
    List,
    Optional,
    Set,
    Tuple,
    Union,
)


class alias(auto):
    def __init__(self, *aliases):
        if len(aliases) == 0:
            raise ValueError("Cannot have empty alias() call.")
        for a in aliases:
            if not isinstance(a, str):
                raise ValueError(
                    f"All aliases for must be strings; found alias of type {type(a)} having value: {a}"
                )
        self.names = aliases
        self.enum_name = None

    def __repr__(self) -> str:
        return str(self)

    def __str__(self):
        if self.enum_name is not None:
            return self.enum_name
        return self.alias_repr

    @property
    def alias_repr(self) -> str:
        return str(f"alias:{list(self.names)}")

    def __setattr__(self, attr_name: str, attr_value: Any):
        if attr_name == "value":
            ## because alias subclasses auto and does not set value, enum.py:143 will try to set value
            self.enum_name = attr_value
        else:
            super(alias, self).__setattr__(attr_name, attr_value)

    def __getattribute__(self, attr_name: str):
        """
        Refer these lines in Python 3.10.9 enum.py:

        class _EnumDict(dict):
            ...
            def __setitem__(self, key, value):
                ...
                elif not _is_descriptor(value):
                    ...
                    if isinstance(value, auto):
                        if value.value == _auto_null:
                            value.value = self._generate_next_value(
                                    key,
                                    1,
                                    len(self._member_names),
                                    self._last_values[:],
                                    )
                            self._auto_called = True
                        value = value.value
                    ...
                ...
            ...

        """
        if attr_name == "value":
            if object.__getattribute__(self, "enum_name") is None:
                ## Gets _auto_null as alias inherits auto class but does not set `value` class member; refer enum.py:142
                try:
                    return object.__getattribute__(self, "value")
                except Exception:
                    from enum import _auto_null

                    return _auto_null
            return self
        return object.__getattribute__(self, attr_name)


_DEFAULT_REMOVAL_TABLE = str.maketrans(
    "ABCDEFGHIJKLMNOPQRSTUVWXYZ",
    "abcdefghijklmnopqrstuvwxyz",
    " -_.:;,",  ## Will be removed
)


class AutoEnum(str, Enum):
    """
    Ultra-fast AutoEnum with fuzzy matching and aliases.
    """

    __slots__ = ()  # no per-instance attrs beyond those in Enum/str

    def __init__(self, value: Union[str, alias]):
        # store aliases tuple for each member
        object.__setattr__(self, "aliases", tuple(value.names) if isinstance(value, alias) else ())

    def _generate_next_value_(name, start, count, last_values):
        # keep the enum member’s *name* as its value
        return name

    @classmethod
    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        setattr(cls, "_lookup_lock", threading.Lock())
        cls._initialize_lookup()

    @classmethod
    def _initialize_lookup(cls):
        # quick check to avoid locking if already built
        if "_value2member_map_normalized_" in cls.__dict__:
            return
        with cls._lookup_lock:
            if "_value2member_map_normalized_" in cls.__dict__:
                return

            mapping: Dict[str, "AutoEnum"] = {}

            def _register(e: "AutoEnum", norm: str):
                if norm in mapping:
                    raise ValueError(
                        f'Cannot register enum "{e.name}"; normalized name "{norm}" already exists.'
                    )
                mapping[norm] = e

            # walk every member exactly once
            for e in cls:
                # register its own name
                _register(e, cls._normalize(e.name))
                # register alias repr
                if e.aliases:
                    # inline alias_repr
                    alias_repr = f"alias:{list(e.aliases)}"
                    _register(e, cls._normalize(alias_repr))
                    # register each plain alias
                    for a in e.aliases:
                        _register(e, cls._normalize(a))

            # stash it on the class
            setattr(cls, "_value2member_map_normalized_", mapping)

    @classmethod
    @lru_cache(maxsize=None)
    def _normalize(cls, x: str) -> str:
        # C-level translate is very fast; caching makes repeated lookups O(1)
        return str(x).translate(_DEFAULT_REMOVAL_TABLE)

    @classmethod
    def _missing_(cls, enum_value: Any):
        # invoked by Enum machinery when auto-casting fails
        return cls.from_str(enum_value, raise_error=True)

    def __str__(self) -> str:
        return self.name

    def __repr__(self) -> str:
        return self.name

    def __hash__(self) -> int:
        return hash(self.__class__.__name__ + "." + self.name)

    def __eq__(self, other: Any) -> bool:
        # identity check is fastest and correct for singletons
        return self is other

    def __ne__(self, other: Any) -> bool:
        return self is not other

    @classmethod
    def from_str(cls, enum_value: Any, raise_error: bool = True) -> Optional["AutoEnum"]:
        # short‐circuit if it's already the right type
        if isinstance(enum_value, cls):
            return enum_value
        # None tolerated?
        if enum_value is None:
            if raise_error:
                raise ValueError("Cannot convert None to enum")
            return None
        # wrong type?
        if not isinstance(enum_value, str):
            if raise_error:
                raise ValueError(f"Input must be str or {cls.__name__}; got {type(enum_value)}")
            return None
        # one normalized dict lookup
        norm = cls._normalize(enum_value)
        e = cls._value2member_map_normalized_.get(norm)
        if e is None and raise_error:
            raise ValueError(f"Could not find enum with value {enum_value!r}; available: {list(cls)}")
        return e

    def matches(self, enum_value: str) -> bool:
        return self is self.from_str(enum_value, raise_error=False)

    @classmethod
    def matches_any(cls, enum_value: str) -> bool:
        return cls.from_str(enum_value, raise_error=False) is not None

    @classmethod
    def does_not_match_any(cls, enum_value: str) -> bool:
        return not cls.matches_any(enum_value)

    @classmethod
    def display_names(cls, **kwargs) -> str:
        return str([e.display_name(**kwargs) for e in cls])

    def display_name(self, *, sep: str = " ") -> str:
        return sep.join(
            word.lower() if word.lower() in ("of", "in", "the") else word.capitalize()
            for word in self.name.split("_")
        )

    # -------------- conversion utilities (unchanged) --------------

    @classmethod
    def convert_keys(cls, d: Dict) -> Dict:
        out = {}
        for k, v in d.items():
            if isinstance(k, str):
                e = cls.from_str(k, raise_error=False)
                out[e] = v if e else v
            else:
                out[k] = v
        return out

    @classmethod
    def convert_keys_to_str(cls, d: Dict) -> Dict:
        return {(str(k) if isinstance(k, cls) else k): v for k, v in d.items()}

    @classmethod
    def convert_values(
        cls, d: Union[Dict, Set, List, Tuple], raise_error: bool = False
    ) -> Union[Dict, Set, List, Tuple]:
        if isinstance(d, dict):
            return cls.convert_dict_values(d)
        if isinstance(d, list):
            return cls.convert_list(d)
        if isinstance(d, tuple):
            return tuple(cls.convert_list(list(d)))
        if isinstance(d, set):
            return cls.convert_set(d)
        if raise_error:
            raise ValueError(f"Unsupported type: {type(d)}")
        return d

    @classmethod
    def convert_dict_values(cls, d: Dict) -> Dict:
        return {k: (cls.from_str(v, raise_error=False) if isinstance(v, str) else v) for k, v in d.items()}

    @classmethod
    def convert_list(cls, l: List) -> List:
        return [
            (cls.from_str(item) if isinstance(item, str) and cls.matches_any(item) else item) for item in l
        ]

    @classmethod
    def convert_set(cls, s: Set) -> Set:
        out = set()
        for item in s:
            if isinstance(item, str) and cls.matches_any(item):
                out.add(cls.from_str(item))
            else:
                out.add(item)
        return out

    @classmethod
    def convert_values_to_str(cls, d: Dict) -> Dict:
        return {k: (str(v) if isinstance(v, cls) else v) for k, v in d.items()}


def make_autoenum(name: str, values: List[str]) -> type[AutoEnum]:
    """
    Dynamically creates an AutoEnum subclass named `name` from a list of strings.
    """

    # sanitize Python identifiers: letters, digits and underscores only
    def to_identifier(s: str) -> str:
        # replace non-word chars with underscore, strip leading digits
        ident: str = re.sub(r"\W+", "_", s).lstrip("0123456789").lstrip("_").rstrip("_")
        ident_capitalize: str = "_".join([x.capitalize() for x in ident.split("_")])
        if s != ident:
            warnings.warn(
                f"We have converted '{s}' to '{ident_capitalize}' to make it a valid Python identifier"
            )
        return ident_capitalize

    members = {to_identifier(v): auto() for v in values}
    # Enum functional constructor:
    return AutoEnum(name, members)
