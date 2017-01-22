import sys

from components.register import Register
from components.memory import Memory

from components.instructions import instructions, InstructionException

class OctoEngine:
    def __init__(self):
        self.halted = False
        self.comparisons = {"JE":False, "JG":False, "JL":False}
        
        self.memory = Memory()
        self.call_stack = []
        
        self.reg_a = Register("A")
        self.reg_b = Register("B")
        self.reg_counter = Register("COUNTER")
        self.instruction_register = Register("INST")
        self.reg_func = Register("FUNC")
        
        self.memory.reserve(255, self.reg_a)
        self.memory.reserve(254, self.reg_b)
        self.memory.reserve(253, self.reg_counter)
        self.memory.reserve(252, self.instruction_register)
        self.memory.reserve(251, self.reg_func)

    def load(self, bytestream):
        for index, byte in enumerate(bytestream):
            self.memory[index] = byte
        
    def instruction_cycle(self):
        instruction = self.memory[self.instruction_register.value] & 0b0111_1111
        if not instruction in instructions:
            raise InstructionException(f"Undefined instruction: {instruction} at memory address {self.instruction_register.value}")
        mem_flag = (self.memory[self.instruction_register.value] & 0b1000_0000) >> 7
        self.instruction_register += 1
        data = self.memory[self.instruction_register]
        self.instruction_register += 1
        instructions[instruction](self, mem_flag, data)
        # print(f"Registers: A:{self.reg_a.value}, B:{self.reg_b.value}, F:{self.reg_func.value}")
        
    def run(self):
        while not self.halted:
            self.instruction_cycle()
            
    def halt(self):
        self.halted = True
        


if __name__ == "__main__":
    emulator = OctoEngine()
    if len(sys.argv) > 1:
        with open(sys.argv[1], "rb") as input_file:
            emulator.load(input_file.read())
    else:
        print("No input file")
    emulator.run()