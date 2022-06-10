# NilNovi Compiler & VM
NNP Compiler - TLC course project 2021/2022

This project contains a compiler and a virtual machine (VM) for the NNP language. The compiler turns the program into object code that can be executed by the VM.

## How to use
Compile your code using
```shell
python3 src/anasyn.py yourprogram.nno -o output.out
```

Execute your compiled code using
```shell
python3 src/vm.py output.out
```

use -h for more information
