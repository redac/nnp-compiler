# NilNovi Compiler & VM
NNP Compiler - Language theory and compilation course project 2021/2022

This project contains a compiler and a virtual machine (VM) for the NNP language. The compiler turns the program into object code that can be executed by the VM.

## How to use
Compile your NNP code using the following command : 
```shell
python3 src/anasyn.py yourprogram.nno -o output.out
```

Run your compiled NNP code using
```shell
python3 src/vm.py output.out
```

use the `-h` flag to display help and more information regarding the commands.

For more information on the source code, visit the [wiki](https://github.com/redac/nnp-compiler/wiki).
