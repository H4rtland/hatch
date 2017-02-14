import sys

sys.path.append("../compiler/hc")
import hc
from compiler.instructions import Instruction

sys.path.append("../vm")
import vm

hatch = """
import io;

function int main() {
    for(let int i=0; i<10; i=i+1) {
        print(i);
    }
}
"""

def test_for():
    instructions = hc.compile(hatch)
    
    virtual_machine = vm.OctoEngine(True)
    virtual_machine.load(instructions)
    output = virtual_machine.run()
    assert output == [i for i in range(0, 10)]