import sys

sys.path.append("../compiler/hc")
import hc
from compiler.instructions import Instruction

sys.path.append("../vm")
import vm

hatch = """
import io;

function void main() {
    let string hello = "Hello, world!";
    print_string(hello);
    print_char(hello[1]);
}
"""

def test_recursion():
    instructions = hc.compile(hatch)
    
    virtual_machine = vm.OctoEngine(True)
    virtual_machine.load(instructions)
    output = virtual_machine.run()
    assert output == list("Hello, world!\ne")