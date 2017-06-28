import hc
import vm

hatch = """
import io;

function int main() {
    let int x = 5;
    io.print(x);
}
"""

def test_compile():
    instructions = hc.compile(hatch)
    
    virtual_machine = vm.OctoEngine(True)
    virtual_machine.load(instructions)
    output = virtual_machine.run()
    assert output == [5,]