from compile.hc import hc
from hvm import vm

hatch = """
import io;

function void main() {
    let int x = 52;
    let int index = 0;
    let int[5] array = [51, x, 53, 54, 55];
    array[4] = 60;
    array[index] = 0;
    for (let int i=0; i<5; i=i+1) {
        print(array[i]);
    }
}
"""

def test_array():
    instructions = hc.compile(hatch)
    
    virtual_machine = vm.OctoEngine(True)
    virtual_machine.load(instructions)
    output = virtual_machine.run()
    assert output == [0, 52, 53, 54, 60]