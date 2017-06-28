from components.register import Register
import itertools

class MemoryAccessException(Exception):
    pass

class Memory:
    def __init__(self, vm):
        self.vm = vm
        self.memory = [0 for i in range(0, 256)]
        self.reserved = {}
        
    def reserve(self, addr, register):
        self.reserved[addr] = register
        

    def __getitem__(self, index):
        if not isinstance(index, (int, Register)):
            raise MemoryAccessException(f"Non integer access to memory ({index.__class__.__name__}: {index})")
        if type(index) is Register:
            index = index.value
        if not 0 <= index <= 255:
            raise MemoryAccessException("Out of bounds memory access")
        if index in self.reserved:
            return self.reserved[index]
        return self.memory[index]
    
    def __setitem__(self, index, value):
        if not isinstance(index, int):
            raise MemoryAccessException(f"Non integer access to memory ({index.__class__.__name__}: {index})")
        #if index in self.reserved:
        #    raise MemoryAccessException(f"Accessing reserved memory ({index})")
        if not 0 <= index <= 255:
            raise MemoryAccessException(f"Out of bounds memory access (at byte {index})")
        
        if not isinstance(value, (int, Register)):
            raise MemoryAccessException(f"Tried to store a non int/register in memory ({value.__class__.__name__}: {value})")
        if isinstance(value, Register):
            value = value.value
        if not 0 <= value <= 255:
            raise MemoryAccessException(f"Tried to store an out of bounds value in memory ({value.__class__.__name__}: {value})")

        self.memory[index] = value
        
    def __repr__(self):
        # Print memory up to unused zeroes
        return f"<Memory: {list(reversed(list(itertools.dropwhile(lambda x: x == 0, reversed(self.memory)))))}>"