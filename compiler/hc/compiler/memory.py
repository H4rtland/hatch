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
    
class Namespace:
    def __init__(self, parent, memory):
        self.parent = parent
        self.memory = memory
        self.locals = {}
        
    def let(self, name, length, var_type):
        #print(f"Allocating variable {name} in namespace")
        addr = self.memory.allocate(length, var_type)
        self.locals[name] = addr
        return addr
    
    def get_namespace(self):
        if self.parent is None:
            return self.locals
        namespace = self.parent.get_namespace()
        namespace.update(self.locals)
        return namespace