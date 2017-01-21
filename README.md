# hatch

[![](https://tokei.rs/b1/github/H4rtland/hatch?category=code)](https://github.com/H4rtland/hatch)

8 bit language, compiler, virtual machine.

## Instruction set

The instruction set can address 256 bytes of memory, as each "single" instruction is stored in a pair of memory bytes, the first being the instruction and the second the data.
The virtual machine's instruction register advances two bytes in memory in each clock cycle. 

    LDB [28] ; load byte in memory address 28 into register B
    
becomes

    10000010    <- load into B, first bit signifies memory address
    00011100    <- number 28

The highest bit in the instruction byte determines whether the following data byte refers to a location in memory or a literal value.

## Hatch

Hatch syntax is similar to any generic C style language, and functions and variables are declared by _function_ and _let_ statements.

    function void main() {
        let int x = 0;
    }
    
The first hatch program that was successfully compiled and run was

    // testfile.hatch
    
    function void main() {
        let int x = 1;
        x = 16;
        let int y = 5;
        y = x + y;
        print(x, y);
    }
    
#### Namespaces

Because the target platform, the virtual machine, has a fixed amount of RAM and only runs a single program at a time, the option exists to manage memory at compile time.

Each block of code has a local namespace, which inherits from the namespace of its parent block.
A variable declaration in a child block is **not** shared with parent blocks.

At the end of a block, all local variables in that namespace are freed from memory.

    // example
    let int x = 5;
    
    if (true) {
        x = 6;          // x is inherited from parent namespace 
        print(x);       // -> 6
    }
    
    print(x);           // -> 6
    
    if (true) {
        let int x = 12; // this block now has a local 'x'
        print(x);       // -> 12
    }
    
    print(x);           // -> 6