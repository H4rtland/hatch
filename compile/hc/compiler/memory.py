import uuid

class DataAddress:
    def __init__(self, addr):
        self.addr = addr
        
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
        
    def let(self, name, length, var_type):
        # addr = self.memory.allocate(length, var_type)
        self.locals[name] = uuid.uuid4().hex
        self.types[name] = var_type
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
    
    def exists(self, name):
        return name in self.get_namespace()
    
    def get_type(self, variable):
        return self.types[variable]