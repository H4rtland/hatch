import sys

from components.register import Register
from components.memory import Memory

from components.instructions import instructions, InstructionException

import settings

class OctoEngine:
    def __init__(self, redirect_output=False):
        self.halted = False
        self.redirect_output = redirect_output
        self.output = []
        
        self.comparisons = {"JE":False, "JG":False, "JL":False}
        
        self.memory = Memory(self)
        self.stack = []
        self.call_stack = []
        self.memory_map = {}

        self.read_buffer = []
        
        
        self.reg_a = Register("A")
        self.reg_b = Register("B")
        self.reg_counter = Register("COUNTER")
        self.instruction_register = Register("INST")
        self.reg_func = Register("FUNC")
        self.reg_offset = Register("OFFSET")
        
        self.memory.reserve(255, self.reg_a)
        self.memory.reserve(254, self.reg_b)
        self.memory.reserve(253, self.reg_counter)
        self.memory.reserve(252, self.instruction_register)
        self.memory.reserve(251, self.reg_func)
        self.memory.reserve(250, self.reg_offset)
        
        self.program_end = 0

    def load(self, bytestream):
        for index, byte in enumerate(bytestream):
            self.memory[index] = byte
        self.program_end = len(bytestream)
        for i in range(self.program_end, 256-16):
            self.memory_map[i] = False
        
        
    def instruction_cycle(self):
        start_instruction_register_value = self.instruction_register.value
        instruction = self.memory[self.instruction_register.value] & 0b0001_1111
        if not instruction in instructions:
            raise InstructionException(f"Undefined instruction: {instruction} at memory address {self.instruction_register.value}")
        mem_flag = (self.memory[self.instruction_register.value] & 0b1000_0000) >> 7
        stack_flag = (self.memory[self.instruction_register.value] & 0b0100_0000) >> 6
        self.instruction_register += 1
        data = self.memory[self.instruction_register]
        self.instruction_register += 1
        instructions[instruction](self, mem_flag, stack_flag, data)
        #print(sum([1 if not b == 0 else 0 for b in self.memory.memory[self.program_end:]])/len(self.memory.memory[self.program_end:]), len(self.memory.memory[self.program_end:]), len(self.stack))
        if settings.debug:
            print(f"Registers: A:{self.reg_a.value}, B:{self.reg_b.value}, F:{self.reg_func.value}, O:{self.reg_offset.value}, I:{start_instruction_register_value}")
            print(f"Stack: {self.stack}")
            length = 256-16-self.program_end
            length = min(20, length)
            print(f"Mem: {self.memory.memory[self.program_end:self.program_end+length]}")
            if settings.step:
                input()
            else:
                print()
        
    def run(self):
        while not self.halted:
            self.instruction_cycle()
        return self.output
            
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