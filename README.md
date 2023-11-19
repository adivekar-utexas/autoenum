# AutoEnum
A fuzzy-matching, Pydantic compatible enum library for Python 3.

## What's an AutoEnum?
`AutoEnum` is a replacement for Python's `Enum`, which has [many problems](https://www.acooke.org/cute/Pythonssad0.html). 

The main problem is that the standard way of defining enums is not Pythonic:
```
from enum import Enum
class Animal(Enum):
    Antelope = 1
    Bandicoot = 2
    Cat = 3
    Dog = 4
```

A while ago, Python 3 introduced the `auto` function to automatically assign values, which was an improvement:
```
from enum import Enum, auto
class Animal(Enum):
    Antelope = auto()
    Bandicoot = auto()
    Cat = auto()
    Dog = auto()
```
But inbuilt Python enums still have a lot of problems:
- Case-sensitivity
- No fuzzy-matching
- No support for aliases
- Incompatible str() and repr() outputs
- No [Pydantic](https://pypi.org/project/pydantic/) compatibility
  
The `autoenum` library fixes all these problems. It is a single-file library with behavior very similar to `auto()` usage above:
```
from autoenum import AutoEnum, auto
class Animal(AutoEnum):   ## Only the superclass is changed.
    Antelope = auto()
    Bandicoot = auto()
    Cat = auto()
    Dog = auto()
```
AutoEnum allows you to do things like this:
```
>>> Animal.Antelope   ## Default usage, recommended in main codebase
Antelope

>>> Animal('Antelope')  ## Fuzzy-match a string entered by a user
Antelope

>>> Animal('     antElope ')  ## Spacing & casing  is handled
Antelope

>>> Animal('Jaguar')  ## Throws an error 
ValueError: Could not find enum with value Jaguar; available values are: [Antelope, Bandicoot, Cat, Dog].

>>> Animal.from_str('Jaguar', raise_error=False)  ## The error can be suppressed
None
```
Accessing an enum value directly, e.g. `Animal.Antelope`, carries the same overhead as a normal enum access (~50 nanoseconds).
Fuzzy matching runs very fast (~750,000 lookups/second on a 26-item enum for the default fuzzy-matching algorithm). 
AutoEnum has been used for years in production systems, and has only gotten faster over time.

## Feature-list

Lets describe the features of AutoEnum. We will use 26 US cities and their aliases as our example:
```
from autoenum import AutoEnum, auto, alias
class City(AutoEnum):
    Atlanta = auto()
    Boston = auto()
    Chicago = auto()
    Denver = auto()
    El_Paso = auto()
    Fresno = auto()
    Greensboro = auto()
    Houston = auto()
    Indianapolis = auto()
    Jacksonville = auto()
    Kansas_City = auto()
    Los_Angeles = auto()
    Miami = auto()
    New_York_City = alias('New York', 'NYC')
    Orlando = auto()
    Philadelphia = auto()
    Quincy = auto()
    Reno = auto()
    San_Francisco = auto()
    Tucson = auto()
    Union_City = auto()
    Virginia_Beach = auto()
    Washington = alias('Washington D.C.')
    Xenia = auto()
    Yonkers = auto()
    Zion = auto()
```

### Construct Enum from string
In regular Python enums, its impossible to directly create the enum value from a string: you have to match it with every possible value.
With an AutoEnum, you can just do:
```
>>> City('Boston')
Boston
```

Which functions the same as:
```
>>> City.Boston
Boston
```

### `is` and `==`
Both `is` and `==` can be used, as with current Enums:
```
>>> City.Los_Angeles is City('Los_Angeles')
True
>>> City.Los_Angeles == City('Los_Angeles')
True
```

In Python code (if statements etc), it is prefered to match using `is`:
```
city = ... ## From previous code
if city is City.Boston:
    ...
```

### Robust to naming conventions
Different teams use different naming-conventions for their enums: 
- Some use `NamesLikeThis` (PascalCase; class-name convention)
- Others use `NAMES_LIKE_THIS` (Java and C++ enum convention)
- Some even use `namesLikeThis` (camelCase; JS convention)
- I somtimes use `Names_Like_this` for proper nouns (for example `Los_Angeles` above).
Its difficult to remember which convention is followed by each project, and sometimes in your own code. 

AutoEnum accepts all the above conventions and gives you the enum value you need:
```
>>> City.Los_Angeles == City('Los_Angeles') == City('LosAngeles') == City('LOS_ANGELES') == City('losAngeles')
True
```

### Fuzzy-matching
In most applications, you use an enum to match as user-entered input. Thus, the string value from which you construct and enum is likely to have minor typos like spacing, underscores, hyphens, or extra periods. 
In inbuilt enums, cleaning of the input must be done separately for every enum. 
With AutoEnum, forget about cleaning. So long as you have the same alphabets in the same order, it will work.
```
>>> City.Los_Angeles == City('Los Angeles') == City('Los__Angeles') == City(' _Los_Angeles   ') == City('LOS-Angeles')
True
```
However, typos such missing chars, extra or modified chars are not permitted, as they can change the meaning of the enum (for example, `Face` vs `Fate` vs `Fat`).
```
>>> City('Lozz Angeles')
ValueError: Could not find enum with value Lozz Angeles; available values are: [Atlanta, Boston, Chicago, Denver, El_Paso, Fresno, Greensboro, Houston, Indianapolis, Jacksonville, Kansas_City, Los_Angeles, Miami, New_York_City, Orlando, Philadelphia, Quincy, Reno, San_Francisco, Tucson, Union_City, Virginia_Beach, Washington, Xenia, Yonkers, Zion].
```

By default, the following characters are ignored:
`(' ', '-', '_', '.', ':', ';', ',')`

You can also write your own fuzzy-matching logic by overriding `_normalize`:

```
class Animal(AutoEnum):
    Antelope = auto()
    Bandicoot = auto()
    Cat = alias('Feline')
    Dog = auto()

    @classmethod
    def _normalize(cls, x: str) -> str:
      return str(x)  ## Exact matching
```

### Aliasing
Python enums, contrary to belief, *do* support aliasing, but it is not a well-known feature:
```
from enum import Enum
class Animal(Enum):
    Antelope = 1
    Bandicoot = 2
    Cat = 3
    Feline = 3  ## Same number as before indicates an alias
    Dog = 4
```
It is not possible to mix the `auto` keyword with this style of aliasing in Python enums. 

In AutoEnum, the `alias` function allows you to create aliases for an enum value:
```
from autoenum import AutoEnum, auto, alias
class Animal(AutoEnum):
    Antelope = auto()
    Bandicoot = auto()
    Cat = alias('Feline')
    Dog = auto()
```
Then you can do:
```
>>> Animal('Cat')
Cat

>>> Animal('Feline')
Cat
```
In code which consumes the alias, you should use `Animal.Cat` everywhere. 

If you are parsing addresses, it is pretty common to see multiple variants of city names, and aliases become very useful:

```
>>> City('Washington') == City('Washington DC') == City('Washington D.C.')
Washington
```

### Pydantic compatibility
You can use AutoEnum directly in [Pydantic](https://pypi.org/project/pydantic/) BaseModels alongside other Pydantic type-verification:
```
from pydantic import BaseModel, conint, confloat, constr
class Company(BaseModel):
    name: constr(min_length=1)
    headquarters: City   ## AutoEnum 
    num_employees: conint(ge=1)
```

When creating such a Pydantic object, you can pass either the enum value, or a string which is fuzzy-matched:
```
>>> netflix = Company(name='Netflix', headquarters='Los Angeles', num_employees=12_000)
>>> netflix.json()
{"name": "Netflix", "headquarters": "Los_Angeles", "num_employees": 12000}
>>> if City(json.loads(netflix.json())['headquarters']) is City.Los_Angeles:
...     print(f'Headquarters is in "{City.Los_Angeles}"')
Headquarters is in "Los_Angeles"
```


### Unified str() and repr()
Inbuilt Python Enums have a fairly gaudy string representation:
```
>>> str(City.Boston)
'City.Boston'
>>> repr(City.Boston)
'<City.Boston: 2>'  ## why?
```
It's usually clear from context that `Boston` belongs to the `City` enum, we don't need `City.Boston`. `2` is also conveying no information here. 

AutoEnums are printed and represented in a minmial, uniform fashion:
```
>>> str(City.Boston)
'Boston'
>>> repr(City.Boston)
'Boston'
```
