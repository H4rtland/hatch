import hc
import vm

hatch = """import io;

function void main() {
    let int[3] numbers = [1, 2, 3];
    print(sum2(numbers));
    print(sum(numbers));
}


function int sum(int[] numbers) {
    let int total = 0;
    for (let int i=0; i<numbers; i=i+1) {
        total = total + numbers[i];
    }
    return total + sum2(numbers);
}

function int sum2(int[] numbers) {
    let int total = 0;
    for (let int i=0; i<numbers; i=i+1) {
        total = total + numbers[i];
    }
    return total;
}"""

def test_pass_array():
    instructions = hc.compile(hatch)
    
    virtual_machine = vm.OctoEngine(True)
    virtual_machine.load(instructions)
    output = virtual_machine.run()
    assert output == [6, 12]