# hatch

[![](https://tokei.rs/b1/github/H4rtland/hatch?category=code)](https://github.com/H4rtland/hatch)

## Instruction set

The instruction set can address 256 bytes of memory, as each "single" instruction is stored in a pair of memory bytes, the first being the instruction and the second the data.
The virtual machine's instruction register advances two bytes in memory in each clock cycle. 

The highest three bits in the instruction byte determines how the data value is interpreted, see documentation at [compiler/hc](https://github.com/H4rtland/hatch/tree/master/compiler/hc).

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

Each block of code has a local namespace, which inherits from the namespace of its parent block.
A variable declaration in a child block is not shared with parent blocks.

At the end of a block, all local variables in that namespace are freed from memory.