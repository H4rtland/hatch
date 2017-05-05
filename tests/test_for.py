import compile.hc.hc as hc
import hvm.vm as vm

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