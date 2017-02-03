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

function void main() {
    let int x = 52;
    let int[5] array = [51, x, 53, 54, 55];
    for (let int i=0; i<5; i=i+1) {
        print(array[i]);
    }
}
"""

def test_for():
    instructions = hc.compile(hatch)
    
    virtual_machine = vm.OctoEngine(True)
    virtual_machine.load(instructions)
    output = virtual_machine.run()
    assert output == [i for i in range(51, 56)]