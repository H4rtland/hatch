import sys
import os.path
import time

from compiler.tokenizer import Tokenizer
from compiler.ast import ASTParser
from compiler.type_checker import TypeChecker
from compiler.assembler import Assembler
from compiler.instructions import Instruction

def compile(source, debug=False, filename="function void main() {}"):
    tokenizer = Tokenizer(source)
    tokens = tokenizer.tokenize()
    
    ast = ASTParser(tokens, source, filename, compiler=[compile, compile_file])
    tree, error = ast.parse()
    
    if error:
        sys.exit()
    
    if debug:
        for trunk in tree:
            trunk.print()
            
    type_checker = TypeChecker(source, tree)
    type_checker.check()
        
    assembler = Assembler(tree)
    instructions, addresses = assembler.assemble()
    if debug:
        return instructions, addresses
    return instructions

def compile_file(filename, debug):
    filename = os.path.abspath(filename)
    with open(filename, "r") as source_file:
        source = source_file.read()
    return compile(source, debug=debug, filename=filename)

if __name__ == "__main__":
    start_time = time.perf_counter()
    instructions, addresses = compile_file("testfile.hatch", True)
    
    with open("testfile.hb", "wb") as output_file:
        output_file.write(bytes(instructions))
        
    with open("testfile.hasm", "w") as output_file:
        output_file.write("; autogenerated assembly\n")
        #output_file.writelines(map(lambda x: str(bin(x)[2:]).zfill(8) + "\n", instructions))
        for i, (op, data) in enumerate(zip(instructions[::2], instructions[1::2])):
            for name, location in addresses.items():
                if i*2 == location:
                    output_file.write(f"{name}:\n")
            surround1, surround2 = "", ""
            if op&0b11000000:
                surround1, surround2 = "[$", "]"
            elif op&0b10000000:
                surround1, surround2 = "[", "]"
            elif op&0b01000000:
                surround1, surround2 = "$", ""
            output_file.write(f"{i*2}: {Instruction(op&0b11111).name} {surround1}{data}{surround2}\n")
    
    duration = time.perf_counter()-start_time
    print(f"Compilation complete, filesize={len(instructions)} bytes, time={duration:.04f} seconds")
