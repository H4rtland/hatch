class RegisterException(Exception):
    pass

class Register:
    def __init__(self, name="register"):
        self.name = name
        self.stored_value = 0
        self.overflow = False

    def load(self, value):
        if not (isinstance(value, int) or isinstance(value, Register)):
            raise RegisterException(f"Register {self.name} set to non integer value ({type(value).__name__}: {value})")
        if isinstance(value, Register):
            value = value.value
        if not 0 <= value <= 255:
            raise RegisterException(f"Loaded value < 0 or > 255 into register {self.name}")
        self.stored_value = value

    @property
    def value(self):
        return self.stored_value

    def __add__(self, register):
        if not type(register) in (int, Register):
            raise RegisterException(f"Addition wasn't an int or other register ({type(register).__name__}: {register})")
        if type(register) is int:
            self.stored_value += register
        elif type(register) is Register:
            self.stored_value += register.value
        
        if self.stored_value > 255:
            self.stored_value %= 255
        elif self.stored_value < 0:
            self.stored_value = (self.stored_value % 255) + 1
        return self

    def __sub__(self, register):
        return self.__add__(-register)

    def __neg__(self):
        self.load((-self.stored_value & 0b11111111) - 1)
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