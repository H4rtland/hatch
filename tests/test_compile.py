import compile.hc.hc as hc
import hvm.vm as vm

hatch = """
import io;

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