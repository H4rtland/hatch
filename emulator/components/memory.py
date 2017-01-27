from components.register import Register

class MemoryAccessException(Exception):
    pass

class Memory:
    def __init__(self):
        self.memory = [0 for i in range(0, 256)]
        self.reserved = {}
        
    def reserve(self, addr, register):
        self.reserved[addr] = register
        

    def __getitem__(self, index):
        if not type(index) in (int, Register):
            raise MemoryAccessException(f"Non integer access to memory ({type(index).__name__}: {index})")
        if type(index) is Register:
            index = index.value
        if not 0 <= index <= 255:
            raise MemoryAccessException("Out of bounds memory access")
        if index in self.reserved:
            return self.reserved[index]
        return self.memory[index]
    
    def __setitem__(self, index, value):
        if not type(index) is int:
            raise MemoryAccessException(f"Non integer access to memory ({type(index).__name__}: {index})")
        #if index in self.reserved:
        #    raise MemoryAccessException(f"Accessing reserved memory ({index})")
        if not 0 <= index <= 255:
            raise MemoryAccessException("Out of bounds memory access")
        
        if not type(value) in (int, Register):
            raise MemoryAccessException(f"Tried to store a non int/register in memory ({type(value).__name__}: {index})")
        if type(value) is Register:
            value = value.value
        if not 0 <= value <= 255:
            raise MemoryAccessException(f"Tried to store an out of bounds value in mempory ({type(value).__name__}: {index})")

        self.memory[index] = value
        
    def __repr__(self):
        return f"<Memory: {self.memory}>"