import hc
import vm

hatch = """
import io;

function void main() {
    let string hello = "Hello!";
    print_string(hello);
    print_char(hello[1]);
    print_string("\nWorld");
    let char H = hello[0];
    print_char(H);
}
"""

def test_string():
    instructions = hc.compile(hatch)
    
    virtual_machine = vm.OctoEngine(True)
    virtual_machine.load(instructions)
    output = virtual_machine.run()
    assert output == list("Hello!\ne\nWorld\nH")