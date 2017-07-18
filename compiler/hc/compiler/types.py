class Type:
    def __init__(self, name, length, indices=None, internal_structure=None):
        self.name = name
        self.length = length
        self.indices = indices
        self.internal_structure = internal_structure or {}
        
    def __repr__(self):
        return f"Type:{self.name}"

    @property
    def has_internal_structure(self):
        return len(self.internal_structure) > 0

class TypeManager1:
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
    INT = Type("int", 1)
    BOOL = Type("bool", 1)
    VOID = Type("void", 1)
    STRING = Type("string", None)
    CHAR = Type("char", 1)

class TypeManager:
    def __init__(self):
        self.defined_types = {}
        for name, attrib in Types.__dict__.items():
            if isinstance(attrib, Type):
                self.define_type(attrib)

    def define_type(self, type_):
        self.defined_types[type_.name] = type_
        return type_

    def get_type(self, type_name):
        if type_name in self.defined_types:
            return self.defined_types[type_name]
        raise Exception(f"Unknown type access \"{type_name}\"")

    def exists(self, type_name):
        return type_name in self.defined_types