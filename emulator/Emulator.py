import sys

from components.register import Register
from components.memory import Memory

from components.instructions import instructions, InstructionException

class OctoEngine:
    def __init__(self):
        self.halted = False
        self.comparisons = {"JE":False, "JG":False, "JL":False}
        
        self.memory = Memory()
        self.reg_a = Register("A")
        self.reg_b = Register("B")
        self.instruction_register = Register("INST")

    def load(self, bytestream):
        for index, byte in enumerate(bytestream):
            self.memory[index] = byte
        
    def instruction_cycle(self):
        if not self.memory[self.instruction_register] in instructions:
            raise InstructionException(f"Undefined instruction: {self.instruction_register.value} at memory address {self.instruction_register.value}")
        instruction = self.memory[self.instruction_register]
        self.instruction_register += 1
        mem_addr = self.memory[self.instruction_register]
        self.instruction_register += 1
        instructions[instruction](self, mem_addr)
        
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
        # print("No input file")
        #       LDA     [10]    LDB     [11]    ADD             PRA            HLT
        inst = [0b0001, 0b1010, 0b0010, 0b1011, 0b0101, 0b0000, 0b011, 0b0000, 0b0110, 0b0000,
                0b1100, 0b0101]
        emulator.load(inst)
    emulator.run()