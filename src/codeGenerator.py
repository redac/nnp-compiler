# Code relatif à la génération de code
class CodeGenerator:

    # Constructeur
    def __init__(self):
        self.generatedCode = []
        self.instrIndex = 0

    ########### Méthodes ###########

    def addCode(self, code):
        self.generatedCode.append((self.instrIndex, code))
        self.instrIndex += 1

    def get_instruction_counter(self):
        return self.instrIndex

    def get_instruction_at_index(self, instrIndex):
        return self.generatedCode[instrIndex]

    def set_instruction_at_index(self, instrIndex, instr):
        self.generatedCode[instrIndex] = (instrIndex,instr)

    def affiche(self):
        for i in range(self.instrIndex):
            print(self.generatedCode[i][1])
