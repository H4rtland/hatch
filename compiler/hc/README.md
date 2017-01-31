# Instructions

### Anatomy of an instruction

    10000110
    |||^^^^^
    |||  |
    |||  ⌞--> Instruction, in this case 00110 = HLT
    ||⌞-----> Unused
    |⌞------> 1 to point data to stack
    ⌞-------> 1 to point data to memory
    
For instructions pointing to the stack, starting with data_byte=1 being the last item on the stack, 2 being the second last etc, the value on the stack is then used as a memory address.