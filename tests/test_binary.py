import hc
import vm

hatch = """
import io;

function int sum(int a, int b) {
    return a + b;
}

function void main() {
    let int[5] array = [11, 22, 33, 44, 55];
    print(array[1]+1);
    print(array[2]-2);

    print(sum(array[0], array[1]));

    print(1+sum(6, 7));
    print(sum(6, 7)+1);

    let int x = 43;
    print(x+5);
    print(x-5);
}
"""

def test_binary():
    instructions = hc.compile(hatch)
    
    virtual_machine = vm.OctoEngine(True)
    virtual_machine.load(instructions)
    output = virtual_machine.run()
    assert output == [23, 31, 33, 14, 14, 48, 38]