import json
import sys
import pytest
from typing import List
from autoenum import AutoEnum, auto, alias

# Try importing pydantic, if not available, we'll skip those tests
try:
    from pydantic import BaseModel, conint, confloat, constr
    PYDANTIC_AVAILABLE = True
except ImportError:
    PYDANTIC_AVAILABLE = False

# Test enums
class Animal(AutoEnum):
    Antelope = auto()
    Bandicoot = auto()
    Cat = alias('Feline')
    Dog = auto()

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

# Only define Pydantic model if Pydantic is available
if PYDANTIC_AVAILABLE:
    class Company(BaseModel):
        name: constr(min_length=1)
        headquarters: City
        num_employees: conint(ge=1)

def test_basic_enum_access():
    """Test basic enum access and comparison"""
    assert Animal.Antelope == Animal('Antelope')
    assert Animal.Bandicoot == Animal('Bandicoot')
    assert Animal.Cat == Animal('Cat')
    assert Animal.Dog == Animal('Dog')

def test_is_operator():
    """Test 'is' operator functionality"""
    assert Animal.Cat is Animal('Cat')
    assert City.Los_Angeles is City('Los_Angeles')
    assert City.Boston is City('Boston')

def test_naming_conventions():
    """Test different naming conventions are handled correctly"""
    assert City.Los_Angeles == City('Los_Angeles') == City('LosAngeles') == City('LOS_ANGELES') == City('losAngeles')
    assert City.New_York_City == City('NewYorkCity') == City('NEW_YORK_CITY') == City('newYorkCity')

def test_fuzzy_matching():
    """Test fuzzy matching with various input formats"""
    assert City.Los_Angeles == City('Los Angeles') == City('Los__Angeles') == City(' _Los_Angeles   ') == City('LOS-Angeles')
    assert City.New_York_City == City('New York') == City('New.York') == City('New-York')
    
    # Test invalid fuzzy matches
    with pytest.raises(ValueError):
        City('Lozz Angeles')
    with pytest.raises(ValueError):
        City('New Yorkk')

def test_aliases():
    """Test alias functionality"""
    assert Animal('Cat') == Animal('Feline')
    assert City('Washington') == City('Washington DC') == City('Washington D.C.')
    assert City('New York') == City('NYC') == City.New_York_City

def test_custom_normalize():
    """Test custom normalization logic"""
    class ExactMatchAnimal(AutoEnum):
        Antelope = auto()
        Bandicoot = auto()
        Cat = alias('Feline')
        Dog = auto()

        @classmethod
        def _normalize(cls, x: str) -> str:
            return str(x)  # Exact matching

    assert ExactMatchAnimal('Antelope') == ExactMatchAnimal.Antelope
    with pytest.raises(ValueError):
        ExactMatchAnimal('antelope')  # Should fail with exact matching

def test_json_compatibility():
    """Test JSON serialization and deserialization"""
    # Test basic JSON serialization
    json_str = json.dumps([Animal.Cat, Animal.Dog])
    assert json_str == '["Cat", "Dog"]'
    
    # Test JSON deserialization
    animals: List[Animal] = Animal.convert_values(json.loads(json_str))
    assert animals == [Animal.Cat, Animal.Dog]
    assert isinstance(animals[0], Animal) and isinstance(animals[1], Animal)

@pytest.mark.skipif(not PYDANTIC_AVAILABLE, reason="Pydantic is not installed")
def test_pydantic_integration():
    """Test Pydantic model integration"""
    # Test with string input
    netflix = Company(name='Netflix', headquarters='Los Angeles', num_employees=12_000)
    assert netflix.headquarters == City.Los_Angeles
    
    # Test JSON serialization
    json_str = netflix.json()
    assert json.loads(json_str)['headquarters'] == 'Los_Angeles'
    
    # Test JSON deserialization
    loaded_company = Company.model_validate_json(json_str)
    assert loaded_company.headquarters == City.Los_Angeles

def test_string_representation():
    """Test string and repr representation"""
    assert str(City.Boston) == 'Boston'
    assert repr(City.Boston) == 'Boston'
    assert str(Animal.Cat) == 'Cat'
    assert repr(Animal.Cat) == 'Cat'

def test_error_handling():
    """Test error handling for invalid inputs"""
    with pytest.raises(ValueError):
        Animal('InvalidAnimal')
    
    with pytest.raises(ValueError):
        City('InvalidCity')
    
    # Test error suppression
    assert Animal.from_str('InvalidAnimal', raise_error=False) is None
    assert City.from_str('InvalidCity', raise_error=False) is None

def test_enum_iteration():
    """Test enum iteration and membership"""
    # Test length of enums
    assert len(list(Animal)) == 4
    assert len(list(City)) == 26
    
    # Test membership of enum values
    assert Animal.Cat in Animal
    assert City.Los_Angeles in City
    
    # For Python 3.12+, test string membership with fuzzy matching
    if sys.version_info >= (3, 12):
        # Test membership using fuzzy matching
        assert 'Cat' in Animal
        assert 'Los Angeles' in City
        assert 'cat' in Animal  # Case insensitive
        assert 'los_angeles' in City  # Case insensitive
        
        # Test membership of aliases
        assert 'Feline' in Animal
        assert 'NYC' in City
        assert 'New York' in City
        
        # Test membership of invalid values
        assert 'InvalidAnimal' not in Animal
        assert 'InvalidCity' not in City
        
        # Test membership with non-string, non-enum values
        assert 123 not in Animal
        assert None not in City
        assert [] not in Animal
        assert {} not in City
    else:
        # For Python < 3.12, verify that string membership raises TypeError
        with pytest.raises(TypeError, match="unsupported operand type\\(s\\) for 'in': 'str' and 'EnumType'"):
            'Cat' in Animal
        with pytest.raises(TypeError, match="unsupported operand type\\(s\\) for 'in': 'str' and 'EnumType'"):
            'Los Angeles' in City 