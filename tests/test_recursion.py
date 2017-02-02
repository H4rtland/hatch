import sys

sys.path.append("../compiler/hc")
import hc
from compiler.instructions import Instruction

sys.path.append("../vm")
import vm

hatch = """
function void print(int n) {
    __internal_print(n);
}

function int triangle_number(int n) {
    if (n == 1) {
        return 1;
    } else {
        return n + triangle_number(n-1);
    }
}

function int main() {
    print(triangle_number(5));
}
"""

def test_recursion():
    instructions = hc.compile(hatch)
    
    virtual_machine = vm.OctoEngine(True)
    virtual_machine.load(instructions)
    output = virtual_machine.run()
    assert output == [15,]