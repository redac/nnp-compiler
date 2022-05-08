# Code relatif à la machine virtuelle qui lit le code généré et l'exécute
import argparse
import re

reg_reserver = re.compile("reserver\(([0-9]+)\)")


class Pile:

    def __init__(self):
        self.valeurs = []

    def empiler(self, valeur):
        self.valeurs.append(valeur)

    def depiler(self):
        if self.valeurs:
            return self.valeurs.pop()

    def estVide(self):
        return self.valeurs == []

    def __str__(self):
        ch = ''
        for x in self.valeurs:
            ch = "|\t" + str(x) + "\t|" + "\n" + ch
        ch = "\nEtat de la pile:\n" + ch
        return ch


class virtual_machine:

    def __init__(self):
        self.po = []  # mémoire de programme

    def init_analyser(self):
        # Partie données
        self.pointeur = 0
        self.pile = Pile()
        # Partie programme
        self.co = 0  # compteur ordinal
        print("VM initialised")
        

    def reserver(self,n):
        self.pointeur += n
        print(str(n)+" emplacement(s) réservés")

    def analyse(self, l):

        if l == "debutProg();":
            self.init_analyser()
        elif reg_reserver.match(l):
            self.reserver(int(reg_reserver.match(l).group(1)))


            


def main():
    parser = argparse.ArgumentParser(
        description='Execute object code.')
    parser.add_argument('inputfile', type=str, nargs=1,
                        help='name of the input source file')
    args = parser.parse_args()

    filename = args.inputfile[0]
    f = None
    try:
        f = open(filename, 'r', encoding="ISO-8859-1")
    except:
        print("Error: can\'t open input file!")
        return

    vm = virtual_machine()

    for line in f:
            line = line.rstrip('\r\n')
            # print(str(line))
            if line != "finProg();":
                vm.analyse(line)
            else:
              return

    f.close()


if __name__ == "__main__":
    main()
