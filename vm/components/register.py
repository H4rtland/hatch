class RegisterException(Exception):
    pass

class Register:
    def __init__(self, name="register"):
        self.name = name
        self.stored_value = 0
        self.overflow = False

    def load(self, value):
        if not (isinstance(value, int) or isinstance(value, Register)):
            raise RegisterException(f"Register {self.name} set to non integer value ({other.__class__.__name__}: {value})")
        if isinstance(value, Register):
            value = value.value
        if not 0 <= value <= 255:
            raise RegisterException(f"Loaded value < 0 or > 255 into register {self.name}")
        self.stored_value = value

    @property
    def value(self):
        return self.stored_value

    def __add__(self, other):
        if not isinstance(other, (int, Register)):
            raise RegisterException(f"Addition wasn't an int or other register ({other.__class__.__name__}: {other})")
        if isinstance(other, int):
            self.stored_value += other
        elif isinstance(other, Register):
            self.stored_value += other.value
        
        if self.stored_value > 255:
            self.stored_value %= 256
        elif self.stored_value < 0:
            self.stored_value = (self.stored_value % 256)
        return self

    def __sub__(self, register):
        return self.__add__(-register)

    def __neg__(self):
        self.load((-self.stored_value & 0b11111111))
        return self
    
    def __mul__(self, other):
        if not isinstance(other, (int, Register)):
            raise RegisterException(f"Addition wasn't an int or other register ({other.__class__.__name__}: {other})")
        if isinstance(other, int):
            self.stored_value *= other
        elif isinstance(other, Register):
            self.stored_value *= other.value
        
        if self.stored_value > 255:
            self.stored_value %= 256
        elif self.stored_value < 0:
            self.stored_value = (self.stored_value % 256)
        return self
    
    def __truediv__(self, other):
        self.__floordiv__(other)
    
    def __floordiv__(self, other):
        if not isinstance(other, (int, Register)):
            raise RegisterException(f"Addition wasn't an int or other register ({other.__class__.__name__}: {other})")
        if isinstance(other, int):
            self.stored_value //= other
        elif isinstance(other, Register):
            self.stored_value //= other.value
        
        if self.stored_value > 255:
            self.stored_value %= 256
        elif self.stored_value < 0:
            self.stored_value = (self.stored_value % 256)
        return self
        
    
    def __and__(self, other):
        return self.value & other
    
    def __or__(self, other):
        return self.value & other
    
    def __eq__(self, other):
        if isinstance(other, int):
            return self.stored_value == other
        elif isinstance(other, Register):
            return self.stored_value == other.stored_value
        return False

    def __repr__(self):
        return f"<Register {self.name}: {self.stored_value}>"