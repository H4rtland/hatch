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

function int main() {
    let int x = 5;
    print(x);
}
"""

def test_compile():
    instructions = hc.compile(hatch)
    
    virtual_machine = vm.OctoEngine(True)
    virtual_machine.load(instructions)
    output = virtual_machine.run()
    assert output == [5,]