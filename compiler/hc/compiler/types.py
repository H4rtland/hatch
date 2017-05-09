class Type:
    def __init__(self, name, length, indices=None):
        self.name = name
        self.length = length
        self.indices = indices
        
    def __repr__(self):
        return f"{self.name}"

class TypeManager:
    defined_types = {}
    
    @staticmethod
    def define_type(type_):
        TypeManager.defined_types[type_.name] = type_
        return type_
        
    @staticmethod
    def get_type(type_name):
        if type_name in TypeManager.defined_types:
            return TypeManager.defined_types[type_name]
        raise Exception(f"Unknown type access \"{type_name}\"")
    
class Types:
    INT = TypeManager.define_type(Type("int", 1))
    BOOL = TypeManager.define_type(Type("bool", 1))
    VOID = TypeManager.define_type(Type("void", 1))
    STRING = TypeManager.define_type(Type("string", None))