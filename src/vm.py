# Code relatif à la machine virtuelle qui lit le code généré et l'exécute
import argparse
import re
import logging

######################REGEXES#####################
reg_reserver = re.compile("reserver\(([0-9]+)\)")
reg_empiler = re.compile("empiler\(([0-9]+)\)")
reg_tze = re.compile("tze\(([0-9]+)\)")
reg_tra = re.compile("tra\(([0-9]+)\)")
reg_erreur = re.compile("erreur\((.*)\)")

logger = logging.getLogger('vm')

DEBUG = True
LOGGING_LEVEL = logging.DEBUG

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
        self.co = 0  # compteur ordinal

    def init_analyser(self):
        # Partie données
        self.pointeur = -1
        self.pile = Pile()
        
        logger.debug("VM initialised")

    def reserver(self, n):
        if n >= 0:
            for i in range(n):
                self.empiler(None)
            logger.debug(str(n)+" emplacement(s) réservés")
        else:
            raise VMException(
                "Reserver: le nombre d'emplacements à réserver doit être positif")

    def empiler(self, val):
        self.pile.empiler(val)
        self.pointeur += 1
        logger.debug(str(val)+" empilé")

    def depiler(self):
        val = self.pile.depiler()
        self.pointeur -= 1
        logger.debug(str(val)+" dépilé")
        return val

    def affectation(self):
        # précondition
        if self.pointeur <= 0:
            raise VMException("Affectation: pile vide")
        val = self.depiler()  # on récupère la valeur à affecter
        ad = self.depiler()  # on récupère l'adresse à affecter
        logger.debug("Pointeur: "+str(self.pointeur))
        logger.debug("Valeur "+str(val)+" affectée à l'adresse "+str(ad))
        # précondition
        if self.pointeur < ad:
            raise VMException("Affectation: adresse incorrecte")
        self.pile.valeurs[ad] = val

    def valeurPile(self):
        # précondition
        if self.pointeur <= 0:
            raise VMException("Valeur pile: pile vide")
        ad = self.depiler()
        if self.pointeur < ad:
            raise VMException("Valeur pile: adresse incorrecte")
        self.empiler(self.pile.valeurs[ad])

    def moins(self):
        if self.pointeur < 0:
            raise VMException("Moins")
        x = self.depiler()
        self.empiler(-x)
        logger.debug("Moins: -"+str(x))

    def add(self):
        # Précondition
        if self.pointeur < 1:
            raise VMException("add")
        a2 = self.depiler()
        a1 = self.depiler()
        self.empiler(a2+a1)
        logger.debug("ADD: "+str(a2)+" + " + str(a1))

    def sous(self):
        # Précondition
        if self.pointeur < 1:
            raise VMException("sous")
        a2 = self.depiler()
        a1 = self.depiler()
        self.empiler(a2-a1)
        logger.debug("SOUS: "+str(a2)+" - " + str(a1))

    def mult(self):
        # Précondition
        if self.pointeur < 1:
            raise VMException("mult")
        a2 = self.depiler()
        a1 = self.depiler()
        self.empiler(a2*a1)
        logger.debug("MULT: "+str(a2)+" x " + str(a1))

    def div(self):
        # Précondition
        if self.pointeur < 1:
            raise VMException("mult")
        a2 = self.depiler()
        a1 = self.depiler()
        self.empiler(a2/a1)
        logger.debug("DIV: "+str(a2)+" / " + str(a1))

    def egal(self):
        # Précondition
        if self.pointeur < 1:
            raise VMException("égal")
        a2 = self.depiler()
        a1 = self.depiler()
        if(a1 == a2):
            self.empiler(1)
        else:
            self.empiler(0)
        logger.debug("EGAL: "+str(a2)+" = " + str(a1))

    def diff(self):
        # Précondition
        if self.pointeur < 1:
            raise VMException("diff")
        a2 = self.depiler()
        a1 = self.depiler()
        if(a1 != a2):
            self.empiler(1)
        else:
            self.empiler(0)
        logger.debug("DIFF: "+str(a2)+" != " + str(a1))

    def inf(self):
        # Précondition
        if self.pointeur < 1:
            raise VMException("inf")
        a2 = self.depiler()
        a1 = self.depiler()
        if(a1 < a2):
            self.empiler(1)
        else:
            self.empiler(0)
        logger.debug("INF: "+str(a2)+" < " + str(a1))

    def infeg(self):
        # Précondition
        if self.pointeur < 1:
            raise VMException("infeg")
        a2 = self.depiler()
        a1 = self.depiler()
        if(a1 <= a2):
            self.empiler(1)
        else:
            self.empiler(0)
        logger.debug("INFEG: "+str(a2)+" <= " + str(a1))

    def sup(self):
        # Précondition
        if self.pointeur < 1:
            raise VMException("sup")
        a2 = self.depiler()
        a1 = self.depiler()
        if(a1 > a2):
            self.empiler(1)
        else:
            self.empiler(0)
        logger.debug("SUP: "+str(a2)+" > " + str(a1))

    def supeg(self):
        # Précondition
        if self.pointeur < 1:
            raise VMException("sup")
        a2 = self.depiler()
        a1 = self.depiler()
        if(a1 >= a2):
            self.empiler(1)
        else:
            self.empiler(0)
        logger.debug("SUPEG: "+str(a2)+" >= " + str(a1))

    def et(self):
        # Précondition
        if self.pointeur < 1:
            raise VMException("et")
        a2 = self.depiler()
        a1 = self.depiler()
        # Précondition
        if (a1 not in {0, 1}) or (a2 not in {0, 1}):
            raise VMException("et: pas des booléens")
        if(a1 and a2):
            self.empiler(1)
        else:
            self.empiler(0)
        logger.debug("ET: "+str(a2)+" et " + str(a1))

    def ou(self):
        # Précondition
        if self.pointeur < 1:
            raise VMException("ou")
        a2 = self.depiler()
        a1 = self.depiler()
        # Précondition
        if (a1 not in {0, 1}) or (a2 not in {0, 1}):
            raise VMException("ou: pas des booléens")
        if(a1 or a2):
            self.empiler(1)
        else:
            self.empiler(0)
        logger.debug("OU: "+str(a2)+" ou " + str(a1))

    def non(self):
        if self.pointeur < 0:
            raise VMException("Non")
        x = self.depiler()
        if x not in {0,1}:
             raise VMException("non: pas un booléen")
        if not x:
            self.empiler(1)
        else:
            self.empiler(0)
        logger.debug("non: not"+str(x))

    def get(self):
        try:
            inputVal = int(input('Input: '))
        except ValueError:
            logger.debug("Not a number")
        ad = self.depiler()  # on récupère l'adresse à affecter
        # précondition
        if self.pointeur < ad:
            raise VMException("GET: adresse incorrecte")
        self.pile.valeurs[ad] = inputVal
        logger.debug(str(self.pile))
    
    def put(self):
        if self.pointeur < 0:
            raise VMException("Put")
        print("OUTPUT: "+str(self.depiler()))

    def tze(self,ad):
        if len(self.po) < ad or 0 > ad :
            raise VMException("TZE: adresse incorrecte :"+str(ad))
        if self.pile.estVide():
            raise VMException("TZE: pile vide")
        #si faux en sommet de pile
        if not self.depiler():
            self.co=ad-1
    
    def tra(self,ad):
        if len(self.po) < ad or 0 > ad :
            raise VMException("TRA: adresse incorrecte")
        self.co=ad-1

    def erreur(self,err):
        print("ERREUR: "+str(err))
        self.po[self.co+1]="finProg();"
        

    def analyse(self, l):
        logger.debug(str(l))
        if l == "debutProg();":
            self.init_analyser()
        elif reg_reserver.match(l):
            self.reserver(int(reg_reserver.match(l).group(1)))
        elif reg_empiler.match(l):
            self.empiler(int(reg_empiler.match(l).group(1)))
        elif l == "affectation()":
            self.affectation()
        elif l == "valeurPile()":
            self.valeurPile()
        elif l == "moins()":
            self.moins()
        elif l == "add()":
            self.add()
        elif l == "sous()":
            self.sous()
        elif l == "mult()":
            self.mult()
        elif l == "div()":
            self.div()
        elif l == "egal()":
            self.egal()
        elif l == "diff()":
            self.diff()
        elif l == "inf()":
            self.inf()
        elif l == "infeg()":
            self.infeg()
        elif l == "sup()":
            self.sup()
        elif l == "supeg()":
            self.supeg()
        elif l == "et()":
            self.et()
        elif l == "ou()":
            self.ou()
        elif l == "get()":
            self.get()
        elif l == "put()":
            self.put()
        elif l == "non()":
            self.non()
        elif reg_tze.match(l):
            self.tze(int(reg_tze.match(l).group(1)))
        elif reg_tra.match(l):
            self.tra(int(reg_tra.match(l).group(1)))
        elif reg_erreur.match(l):
            self.erreur(reg_erreur.match(l).group(1))
        logger.debug("pointeur:  "+str(self.pointeur))
        logger.debug(str(self.pile))
        


def main():
    parser = argparse.ArgumentParser(
        description='Execute object code.')
    parser.add_argument('inputfile', type=str, nargs=1,
                        help='name of the input source file')
    parser.add_argument('-d', '--debug', action='store_const', const=logging.DEBUG,
                        default=logging.INFO, help='show debugging info on output')
    args = parser.parse_args()

    filename = args.inputfile[0]
    f = None
    try:
        f = open(filename, 'r', encoding="ISO-8859-1")
    except:
        logger.debug("Error: can\'t open input file!")
        return
    
    # create logger
    LOGGING_LEVEL = args.debug
    logger.setLevel(LOGGING_LEVEL)
    ch = logging.StreamHandler()
    ch.setLevel(LOGGING_LEVEL)
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    ch.setFormatter(formatter)
    logger.addHandler(ch)

    vm = virtual_machine()


    for line in f:
        line = line.rstrip('\r\n')
        vm.po.append(line)
    logger.debug(vm.po)
    while vm.po[vm.co]!="finProg();":
        vm.analyse(vm.po[vm.co])
        vm.co+=1

    f.close()


if __name__ == "__main__":
    main()
