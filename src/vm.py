# Code relatif à la machine virtuelle qui lit le code généré et l'exécute
import argparse
import re


reg_reserver = re.compile("reserver\(([0-9]+)\)")
reg_empiler = re.compile("empiler\(([0-9]+)\)")


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


class VMException(Exception):
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return repr(self.value)


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

    def reserver(self, n):
        if n >= 0:
            self.pointeur += n
            print(str(n)+" emplacement(s) réservés")
        else:
            raise VMException(
                "Reserver: le nombre d'emplacements à réserver doit être positif")

    def empiler(self, val):
        self.pile.empiler(val)
        self.pointeur += 1
        print(str(val)+" empilé")

    def affectation(self):
        val = self.pile.depiler()  # on récupère la valeur à affecter
        ad = self.pile.depiler()  # on récupère l'adresse à affecter
        # préconditions
        if self.pointeur < ad+2:
            raise VMException("Affectation: adresse incorrecte")

        temp = Pile()
        print("adresse:" + str(ad) + "   valeur: "+str(val))
        print(str(self.pile))
        while len(self.pile.valeurs) != ad:
            # on empile toute la pile dans une pile temporaire
            temp.empiler(self.pile.depiler)
        self.pile.empiler(val)  # on met la valeur à l'adresse indiquée
        temp.depiler()  # on enlève l'ancienne valeur de la variable
        while not temp.estVide():
            self.pile.empiler(temp.depiler)  # on rempile la pile
        self.pointeur -= 2
        print("Valeur :"+str(val)+" affectée à l'adresse: "+str(ad))

    def analyse(self, l):

        if l == "debutProg();":
            self.init_analyser()
        elif reg_reserver.match(l):
            self.reserver(int(reg_reserver.match(l).group(1)))
        elif reg_empiler.match(l):
            self.empiler(int(reg_empiler.match(l).group(1)))
        elif l == "affectation()":
            self.affectation()
        # print(str(self.pile))


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
        print(str(line))
        if line != "finProg();":
            vm.analyse(line)
        else:
            return

    f.close()


if __name__ == "__main__":
    main()
