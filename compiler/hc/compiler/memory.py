import uuid

class DataAddress:
    def __init__(self, uid, offset=0):
        self.uid = uid
        self.offset = offset
        
    def __repr__(self):
        return f"<DataAddress: {self.addr}>"
    
class FunctionAddress:
    def __init__(self, func_name):
        self.func_name = func_name
    
    def __repr__(self):
        return f"<FuncAddress: {self.func_name}>"


class MemoryBlock:
    def __init__(self, length, var_type):
        self.length = length
        self.var_type = var_type
    
    def __repr__(self):
        return f"<MemoryBlock: length {self.length}>"

class MemoryModel:
    def __init__(self):
        self.memory = {}
        self.memory_size = 256
        self.stack = []
        self.temp_extra_stack_vars = 0
        
    def id_on_stack(self, uid):
        #if isinstance(uid, FunctionAddress):
        #    print("Getting ID on stack,", uid)
        #    return uid
        #print(f"Getting ID on stack, uid={uid}, stack={self.stack}, temp_extra={self.temp_extra_stack_vars} -> {len(self.stack)-self.stack.index(uid) + self.temp_extra_stack_vars}")
        return len(self.stack)-self.stack.index(uid) + self.temp_extra_stack_vars
    
    def exists(self, uid):
        return uid in self.stack
        
    def space_is_free(self, at, length):
        for addr, block in self.memory.items():
            a = set(range(at, at+length))
            b = set(range(addr, addr+block.length))
            if len(a & b) > 0:
                return False
        return True
        
    def find_space(self, length):
        for at in range(0, self.memory_size):
            if self.space_is_free(at, length):
                return at
        
    def allocate(self, bytes_, var_type):
        address = self.find_space(bytes_)
        block = MemoryBlock(bytes_, var_type)
        self.memory[address] = block
        return address
    
    def free(self, address):
        if address in self.memory:
            del self.memory[address]
            
    def unstack(self, number):
        self.stack = self.stack[:-number]
    
class Namespace:
    def __init__(self, parent, memory):
        self.parent = parent
        self.memory = memory
        self.locals = {}
        self.globals = {}
        self.types = {}
        self.stack_variables = 0
        self.is_arrays = {}
        
    def let(self, name, length, var_type, is_array):
        # addr = self.memory.allocate(length, var_type)
        self.locals[name] = uuid.uuid4().hex
        self.types[name] = var_type
        self.is_arrays[name] = is_array
        self.stack_variables += 1
        self.memory.stack.append(self.locals[name])
        # print(f"Allocating variable {name} in namespace, {self.locals}, {self.get_namespace()}")
        return self.locals[name]
    
    def get_namespace(self, no_globals=False):
        if self.parent is None:
            if no_globals:
                return {}
            return dict(self.globals)
        namespace = self.parent.get_namespace(no_globals=no_globals)
        namespace.update(self.locals)
        return dict(namespace)
    
    def get_types(self):
        if self.parent is None:
            return self.types
        return {**self.parent.get_types(), **self.types}
    
    def exists(self, name):
        return name in self.get_namespace()
    
    def get_type(self, variable):
        return self.get_types()[variable]
    
    def get_is_arrays(self):
        if self.parent is None:
            return self.is_arrays
        return {**self.parent.get_is_arrays(), **self.is_arrays}
    
    def is_array(self, name):
        return self.get_is_arrays()[name]

class NamespaceGroup:
    def __init__(self, parent, stack):
        self.parent = parent
        self.stack = stack
        self.locals = {}
        self.is_arrays = {}
        self.is_structs = {}
        
    def let(self, name, is_array=False, is_struct=False):
        uid = uuid.uuid4().hex
        self.locals[name] = uid
        self.is_arrays[name] = is_array
        self.is_structs[name] = is_struct
        self.stack.add(uid)
        return uid
        
    def add(self, name, value):
        self.locals[name] = value
        
    def get_namespace(self, no_globals=False):
        if self.parent is None:
            if no_globals:
                return {}
            return dict(self.locals)
        return {**self.parent.get_namespace(no_globals), **self.locals}
    
    def get_is_arrays(self):
        if self.parent is None:
            return self.is_arrays
        return {**self.parent.get_is_arrays(), **self.is_arrays}

    def get_is_structs(self):
        if self.parent is None:
            return self.is_structs
        return {**self.parent.get_is_structs(), **self.is_structs}
    
    def is_array(self, name):
        return self.get_is_arrays()[name]

    def is_struct(self, name):
        return self.get_is_structs()[name]
    
    def get(self, *path_name):
        namespace = self.get_namespace()
        name, *subnames = path_name
        if len(subnames) == 0:
            return namespace[name]
        if isinstance(namespace[name], NamespaceGroup):
            return namespace[name].get(*subnames)
        raise Exception("Path did not exist")
    
    def contains(self, *path_name):
        namespace = self.get_namespace()
        name, *subnames = path_name
        if len(subnames) == 0:
            return name in namespace
        if isinstance(namespace[name], NamespaceGroup):
            return namespace[name].contains(*subnames)
        raise Exception("Path did not exist")

    """def get_matching_function(self, *path_name):
        namespace = self.get_namespace()
        name, *subnames = path_name
        if subnames:"""
        
        
    
        
    
class Stack:
    def __init__(self):
        self.stack = []
        self.temp_extra_stack_vars = 0
        
    def add(self, uid):
        """
        Add a unique identifier to the top of the stack
        :param uid: uid to add
        :return:
        """
        self.stack.append(uid)
        
    def id_on_stack(self, uid):
        """
        Get position of a uid on the stack.
        Top item on the stack returns 1, second item on the stack returns 2.
        :param uid: unique identifier of stack reference
        :return: stack position
        """
        return len(self.stack)-self.stack.index(uid) + self.temp_extra_stack_vars

    def exists(self, uid):
        """
        Check if unique identifier exists on the stack
        :param uid: unique identifier of stack reference
        :return:
        """
        return uid in self.stack
    
    def unstack(self, number):
        """
        Remove the top n  uids from the top of the stack
        :param number: uids to remove from the top of the stack
        :return:
        """
        self.stack = self.stack[:-number]
