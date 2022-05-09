#!/usr/bin/python

# @package anasyn
# Syntactical Analyser package.
#

from ast import While
from hashlib import new
from operator import le
import sys
import argparse
import re
import logging
from tkinter import N

import analex
import codeGenerator

logger = logging.getLogger('anasyn')

DEBUG = True
LOGGING_LEVEL = logging.DEBUG


# Identifier Table declaration
#
# keeps track of semantics of variables i.e. it stores information about the
# scope and binding information about names, information about instances of
# various entities such as variable and function names, classes, objects, etc.
#
# key = object identity (unique)
# ['ident', 'type', @address, []]
#

identifierTable = {}
anyVarsIDs = []    # Stores variables with unknown type


class AnaSynException(Exception):
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return repr(self.value)

########################################################################
# Syntactical Diagrams
########################################################################


# Pour la génération de code
# Chaque ajout de code se fera par cg.addCode("exemple de code objet")
cg = codeGenerator.CodeGenerator()


def program(lexical_analyser):
    specifProgPrinc(lexical_analyser)
    lexical_analyser.acceptKeyword("is")
    cg.addCode("debutProg();")
    corpsProgPrinc(lexical_analyser)


def specifProgPrinc(lexical_analyser):
    lexical_analyser.acceptKeyword("procedure")
    ident = lexical_analyser.acceptIdentifier()
    logger.debug("Name of program : "+ident)
    # key = object identity (unique)
    identifierTable[id(ident)] = [ident, "procedure", len(identifierTable), []]


def corpsProgPrinc(lexical_analyser):
    if not lexical_analyser.isKeyword("begin"):
        logger.debug("Parsing declarations")
        partieDecla(lexical_analyser)
        logger.debug("End of declarations")
        print(identifierTable)
    lexical_analyser.acceptKeyword("begin")

    if not lexical_analyser.isKeyword("end"):
        logger.debug("Parsing instructions")
        suiteInstr(lexical_analyser)
        logger.debug("End of instructions")

    lexical_analyser.acceptKeyword("end")
    lexical_analyser.acceptFel()
    cg.addCode("finProg();")
    logger.debug("End of program")


def partieDecla(lexical_analyser):
    if lexical_analyser.isKeyword("procedure") or lexical_analyser.isKeyword("function"):
        listeDeclaOp(lexical_analyser)
        if not lexical_analyser.isKeyword("begin"):
            listeDeclaVar(lexical_analyser)

    else:
        listeDeclaVar(lexical_analyser)


def listeDeclaOp(lexical_analyser):
    declaOp(lexical_analyser)
    lexical_analyser.acceptCharacter(";")
    if lexical_analyser.isKeyword("procedure") or lexical_analyser.isKeyword("function"):
        listeDeclaOp(lexical_analyser)


def declaOp(lexical_analyser):
    if lexical_analyser.isKeyword("procedure"):
        procedure(lexical_analyser)
    if lexical_analyser.isKeyword("function"):
        fonction(lexical_analyser)


def procedure(lexical_analyser):
    lexical_analyser.acceptKeyword("procedure")
    ident = lexical_analyser.acceptIdentifier()
    identifierTable[id(ident)] = [ident, "procedure", len(identifierTable), []]
    logger.debug("Name of procedure : "+ident)

    partieFormelle(lexical_analyser)

    lexical_analyser.acceptKeyword("is")
    corpsProc(lexical_analyser)


def fonction(lexical_analyser):
    lexical_analyser.acceptKeyword("function")
    ident = lexical_analyser.acceptIdentifier()
    identifierTable[id(ident)] = [ident, "function", len(identifierTable), []]
    logger.debug("Name of function : "+ident)

    partieFormelle(lexical_analyser)

    lexical_analyser.acceptKeyword("return")
    nnpType(lexical_analyser)

    lexical_analyser.acceptKeyword("is")
    corpsFonct(lexical_analyser)


def corpsProc(lexical_analyser):
    if not lexical_analyser.isKeyword("begin"):
        partieDeclaProc(lexical_analyser)
    lexical_analyser.acceptKeyword("begin")
    suiteInstr(lexical_analyser)
    lexical_analyser.acceptKeyword("end")


def corpsFonct(lexical_analyser):
    if not lexical_analyser.isKeyword("begin"):
        partieDeclaProc(lexical_analyser)
    lexical_analyser.acceptKeyword("begin")
    suiteInstrNonVide(lexical_analyser)
    lexical_analyser.acceptKeyword("end")


def partieFormelle(lexical_analyser):
    lexical_analyser.acceptCharacter("(")
    if not lexical_analyser.isCharacter(")"):
        listeSpecifFormelles(lexical_analyser)
    lexical_analyser.acceptCharacter(")")


def listeSpecifFormelles(lexical_analyser):
    specif(lexical_analyser)
    if not lexical_analyser.isCharacter(")"):
        lexical_analyser.acceptCharacter(";")
        listeSpecifFormelles(lexical_analyser)


def specif(lexical_analyser):
    listeIdent(lexical_analyser)
    lexical_analyser.acceptCharacter(":")
    if lexical_analyser.isKeyword("in"):
        mode(lexical_analyser)

    nnpType(lexical_analyser)


def mode(lexical_analyser):
    lexical_analyser.acceptKeyword("in")
    if lexical_analyser.isKeyword("out"):
        lexical_analyser.acceptKeyword("out")
        logger.debug("in out parameter")
    else:
        logger.debug("in parameter")


def nnpType(lexical_analyser):
    # Parses types
    for obj in identifierTable:
        objType = identifierTable[obj][1]
        if objType == "any":
            anyVarsIDs.append(obj)
    print(anyVarsIDs)
    if lexical_analyser.isKeyword("integer"):
        lexical_analyser.acceptKeyword("integer")
        logger.debug("integer type")
        for varID in anyVarsIDs:
            identifierTable[varID][1] = "integer"
    elif lexical_analyser.isKeyword("boolean"):
        lexical_analyser.acceptKeyword("boolean")
        for varID in anyVarsIDs:
            identifierTable[varID][1] = "boolean"
        logger.debug("boolean type")
    else:
        logger.error("Unknown type found <" +
                     lexical_analyser.get_value() + ">!")
        raise AnaSynException("Unknown type found <" +
                              lexical_analyser.get_value() + ">!")


def partieDeclaProc(lexical_analyser):
    listeDeclaVar(lexical_analyser)


def listeDeclaVar(lexical_analyser):
    declaVar(lexical_analyser)
    if lexical_analyser.isIdentifier():
        listeDeclaVar(lexical_analyser)


def declaVar(lexical_analyser):
    n = listeIdent(lexical_analyser)  # nombre de blocks à réserver
    logger.debug(str(n) + " variables")
    lexical_analyser.acceptCharacter(":")
    logger.debug("now parsing type...")
    nnpType(lexical_analyser)
    cg.addCode("réserver("+str(n)+")")
    lexical_analyser.acceptCharacter(";")

# La fonction renvoie le nombre d'éléments de la liste de déclaration


def listeIdent(lexical_analyser):
    n = 1
    ident = lexical_analyser.acceptIdentifier()
    logger.debug("identifier found: "+str(ident))
    # Add variable to the ident table, with an "any" type for now
    identifierTable[id(ident)] = [ident, "any", len(identifierTable), []]
    if lexical_analyser.isCharacter(","):
        lexical_analyser.acceptCharacter(",")
        n = listeIdent(lexical_analyser)+1

    return n


def suiteInstrNonVide(lexical_analyser):
    instr(lexical_analyser)
    if lexical_analyser.isCharacter(";"):
        lexical_analyser.acceptCharacter(";")
        suiteInstrNonVide(lexical_analyser)


def suiteInstr(lexical_analyser):
    if not lexical_analyser.isKeyword("end"):
        suiteInstrNonVide(lexical_analyser)


def instr(lexical_analyser):
    if lexical_analyser.isKeyword("while"):
        boucle(lexical_analyser)
    elif lexical_analyser.isKeyword("if"):
        altern(lexical_analyser)
    elif lexical_analyser.isKeyword("get") or lexical_analyser.isKeyword("put"):
        es(lexical_analyser)
    elif lexical_analyser.isKeyword("return"):
        retour(lexical_analyser)
    elif lexical_analyser.isIdentifier():
        ident = lexical_analyser.acceptIdentifier()
        if lexical_analyser.isSymbol(":="):
            # affectation
            print("table \t"+str(identifierTable))
            print("ident \t"+str(id(ident)))
            addr = identifierTable[id(ident)][2]
            cg.addCode("empiler("+str(addr)+")      //ici")
            lexical_analyser.acceptSymbol(":=")
            expression(lexical_analyser)
            cg.addCode("affectation()")
            logger.debug("parsed affectation")
        elif lexical_analyser.isCharacter("("):
            lexical_analyser.acceptCharacter("(")
            if not lexical_analyser.isCharacter(")"):
                listePe(lexical_analyser)

            lexical_analyser.acceptCharacter(")")
            logger.debug("parsed procedure call")
        else:
            logger.error("Expecting procedure call or affectation!")
            raise AnaSynException("Expecting procedure call or affectation!")

    else:
        logger.error("Unknown Instruction <" +
                     lexical_analyser.get_value() + ">!")
        raise AnaSynException("Unknown Instruction <" +
                              lexical_analyser.get_value() + ">!")


def listePe(lexical_analyser):
    expression(lexical_analyser)
    if lexical_analyser.isCharacter(","):
        lexical_analyser.acceptCharacter(",")
        listePe(lexical_analyser)


def expression(lexical_analyser):
    logger.debug("parsing expression: " + str(lexical_analyser.get_value()))

    exp1(lexical_analyser)
    if lexical_analyser.isKeyword("or"):
        lexical_analyser.acceptKeyword("or")
        exp1(lexical_analyser)
        cg.addCode("or()")


def exp1(lexical_analyser):
    logger.debug("parsing exp1")

    exp2(lexical_analyser)
    if lexical_analyser.isKeyword("and"):
        lexical_analyser.acceptKeyword("and")
        exp2(lexical_analyser)
        cg.addCode("et()")


def exp2(lexical_analyser):
    logger.debug("parsing exp2")

    exp3(lexical_analyser)
    if lexical_analyser.isSymbol("<") or \
            lexical_analyser.isSymbol("<=") or \
            lexical_analyser.isSymbol(">") or \
            lexical_analyser.isSymbol(">="):
        infeg = lexical_analyser.isSymbol("<=")
        inf = lexical_analyser.isSymbol("<")
        sup = lexical_analyser.isSymbol(">")
        opRel(lexical_analyser)
        exp3(lexical_analyser)
        if infeg:
            cg.addCode("infeg()")
        elif inf:
            cg.addCode("inf()")
        elif sup:
            cg.addCode("sup()")
        else:
            cg.addCode("supeg()")
    elif lexical_analyser.isSymbol("=") or \
            lexical_analyser.isSymbol("/="):
        egal = lexical_analyser.isSymbol("=")
        opRel(lexical_analyser)
        exp3(lexical_analyser)
        if egal:
            cg.addCode("egal()")
        else:
            cg.addCode("diff()")


def opRel(lexical_analyser):
    logger.debug("parsing relationnal operator: " +
                 lexical_analyser.get_value())

    if lexical_analyser.isSymbol("<"):
        lexical_analyser.acceptSymbol("<")

    elif lexical_analyser.isSymbol("<="):
        lexical_analyser.acceptSymbol("<=")

    elif lexical_analyser.isSymbol(">"):
        lexical_analyser.acceptSymbol(">")

    elif lexical_analyser.isSymbol(">="):
        lexical_analyser.acceptSymbol(">=")

    elif lexical_analyser.isSymbol("="):
        lexical_analyser.acceptSymbol("=")

    elif lexical_analyser.isSymbol("/="):
        lexical_analyser.acceptSymbol("/=")

    else:
        msg = "Unknown relationnal operator <" + lexical_analyser.get_value() + ">!"
        logger.error(msg)
        raise AnaSynException(msg)


def exp3(lexical_analyser):
    logger.debug("parsing exp3")
    exp4(lexical_analyser)
    if lexical_analyser.isCharacter("+") or lexical_analyser.isCharacter("-"):
        moins = lexical_analyser.isCharacter("-")
        opAdd(lexical_analyser)
        exp4(lexical_analyser)
        if moins:
            cg.addCode("moins()")
        cg.addCode("add()")
        


def opAdd(lexical_analyser):
    logger.debug("parsing additive operator: " + lexical_analyser.get_value())
    if lexical_analyser.isCharacter("+"):
        lexical_analyser.acceptCharacter("+")

    elif lexical_analyser.isCharacter("-"):
        lexical_analyser.acceptCharacter("-")

    else:
        msg = "Unknown additive operator <" + lexical_analyser.get_value() + ">!"
        logger.error(msg)
        raise AnaSynException(msg)


def exp4(lexical_analyser):
    logger.debug("parsing exp4")

    prim(lexical_analyser)
    if lexical_analyser.isCharacter("*") or lexical_analyser.isCharacter("/"):
        fois = lexical_analyser.isCharacter("*")
        opMult(lexical_analyser)
        prim(lexical_analyser)
        if fois:
            cg.addCode("mult()")
        else:
            cg.addCode("div()")


def opMult(lexical_analyser):
    logger.debug("parsing multiplicative operator: " +
                 lexical_analyser.get_value())
    if lexical_analyser.isCharacter("*"):
        lexical_analyser.acceptCharacter("*")

    elif lexical_analyser.isCharacter("/"):
        lexical_analyser.acceptCharacter("/")

    else:
        msg = "Unknown multiplicative operator <" + lexical_analyser.get_value() + ">!"
        logger.error(msg)
        raise AnaSynException(msg)


def prim(lexical_analyser):
    logger.debug("parsing prim")
    moins = False
    non = False
    if lexical_analyser.isCharacter("+") or lexical_analyser.isCharacter("-") or lexical_analyser.isKeyword("not"):
        non = lexical_analyser.isCharacter("not")
        moins = lexical_analyser.isCharacter("-")
        opUnaire(lexical_analyser)
    elemPrim(lexical_analyser)
    if moins:
        cg.addCode("moins()")
    elif non:
        cg.addCode("non()")


def opUnaire(lexical_analyser):
    logger.debug("parsing unary operator: " + lexical_analyser.get_value())
    if lexical_analyser.isCharacter("+"):
        lexical_analyser.acceptCharacter("+")

    elif lexical_analyser.isCharacter("-"):
        lexical_analyser.acceptCharacter("-")

    elif lexical_analyser.isKeyword("not"):
        lexical_analyser.acceptKeyword("not")

    else:
        msg = "Unknown additive operator <" + lexical_analyser.get_value() + ">!"
        logger.error(msg)
        raise AnaSynException(msg)


def elemPrim(lexical_analyser):
    logger.debug("parsing elemPrim: " + str(lexical_analyser.get_value()))
    if lexical_analyser.isCharacter("("):
        lexical_analyser.acceptCharacter("(")
        expression(lexical_analyser)
        lexical_analyser.acceptCharacter(")")
    elif lexical_analyser.isInteger() or lexical_analyser.isKeyword("true") or lexical_analyser.isKeyword("false"):
        valeur(lexical_analyser)
    elif lexical_analyser.isIdentifier():
        ident = lexical_analyser.acceptIdentifier()
        addr=identifierTable[id(ident)][2]-1
        cg.addCode("empiler("+str(addr)+")      //ici")
        cg.addCode("valeurPile()")
        if lexical_analyser.isCharacter("("):			# Appel fonct
            lexical_analyser.acceptCharacter("(")
            if not lexical_analyser.isCharacter(")"):
                listePe(lexical_analyser)

            lexical_analyser.acceptCharacter(")")
            logger.debug("parsed procedure call")

            logger.debug("Call to function: " + ident)
        else:
            logger.debug("Use of an identifier as an expression: " + ident)
            # ...
    else:
        logger.error("Unknown Value!")
        raise AnaSynException("Unknown Value!")


def valeur(lexical_analyser):
    if lexical_analyser.isInteger():
        entier = lexical_analyser.acceptInteger()
        cg.addCode("empiler("+str(entier)+")")
        logger.debug("integer value: " + str(entier))
        return "integer"
    elif lexical_analyser.isKeyword("true") or lexical_analyser.isKeyword("false"):
        vtype = valBool(lexical_analyser)
        return vtype
    else:
        logger.error("Unknown Value! Expecting an integer or a boolean value!")
        raise AnaSynException(
            "Unknown Value ! Expecting an integer or a boolean value!")


def valBool(lexical_analyser):
    if lexical_analyser.isKeyword("true"):
        lexical_analyser.acceptKeyword("true")
        cg.addCode("empiler(1)")
        logger.debug("boolean true value")

    else:
        logger.debug("boolean false value")
        lexical_analyser.acceptKeyword("false")
        cg.addCode("empiler(0)")

    return "boolean"


def es(lexical_analyser):
    logger.debug("parsing E/S instruction: " + lexical_analyser.get_value())
    if lexical_analyser.isKeyword("get"):
        lexical_analyser.acceptKeyword("get")
        lexical_analyser.acceptCharacter("(")
        ident = lexical_analyser.acceptIdentifier()
        addr=identifierTable[id(ident)][2]-1
        cg.addCode("empiler("+str(addr)+")              //ici")
        cg.addCode("get()")
        lexical_analyser.acceptCharacter(")")
        logger.debug("Call to get "+ident)
    elif lexical_analyser.isKeyword("put"):
        lexical_analyser.acceptKeyword("put")
        lexical_analyser.acceptCharacter("(")
        expression(lexical_analyser)
        cg.addCode("put()")
        lexical_analyser.acceptCharacter(")")
        logger.debug("Call to put")
    else:
        logger.error("Unknown E/S instruction!")
        raise AnaSynException("Unknown E/S instruction!")


def boucle(lexical_analyser):
    logger.debug("parsing while loop: ")
    lexical_analyser.acceptKeyword("while")
    ad1 = cg.get_instruction_counter()

    expression(lexical_analyser)

    lexical_analyser.acceptKeyword("loop")
    cg.addCode("tze(ad2); //doit pas apparaitre, remplacer avec ad2")
    index_ad2 = cg.get_instruction_counter()
    suiteInstr(lexical_analyser)

    lexical_analyser.acceptKeyword("end")
    cg.addCode("tra("+str(ad1)+"); //back to loop")
    ad2 = cg.get_instruction_counter()
    cg.set_instruction_at_index(
        index_ad2, "tze("+str(ad2)+"); //loop condition (end)")
    logger.debug("end of while loop ")


def altern(lexical_analyser):
    logger.debug("parsing if: ")
    lexical_analyser.acceptKeyword("if")

    expression(lexical_analyser)

    lexical_analyser.acceptKeyword("then")
    # modifier ad1 pour avoir la bonne addresse
    cg.addCode("tze(ad1); //if")
    suiteInstr(lexical_analyser)

    if lexical_analyser.isKeyword("else"):
        lexical_analyser.acceptKeyword("else")
        cg.addCode("tra(ad2); //else")
        suiteInstr(lexical_analyser)

    lexical_analyser.acceptKeyword("end")
    logger.debug("end of if")


def retour(lexical_analyser):
    logger.debug("parsing return instruction")
    lexical_analyser.acceptKeyword("return")
    expression(lexical_analyser)

########################################################################


def main():

    parser = argparse.ArgumentParser(
        description='Do the syntactical analysis of a NNP program.')
    parser.add_argument('inputfile', type=str, nargs=1,
                        help='name of the input source file')
    parser.add_argument('-o', '--outputfile', dest='outputfile', action='store',
                        default="", help='name of the output file (default: stdout)')
    parser.add_argument('-v', '--version', action='version',
                        version='%(prog)s 1.0')
    parser.add_argument('-d', '--debug', action='store_const', const=logging.DEBUG,
                        default=logging.INFO, help='show debugging info on output')
    parser.add_argument('-p', '--pseudo-code', action='store_const', const=True, default=False,
                        help='enables output of pseudo-code instead of assembly code')
    parser.add_argument('--show-ident-table', action='store_true',
                        help='shows the final identifiers table')
    args = parser.parse_args()

    filename = args.inputfile[0]
    f = None
    try:
        f = open(filename, 'r', encoding="ISO-8859-1")
    except:
        print("Error: can\'t open input file!")
        return

    outputFilename = args.outputfile

    # create logger
    LOGGING_LEVEL = args.debug
    logger.setLevel(LOGGING_LEVEL)
    ch = logging.StreamHandler()
    ch.setLevel(LOGGING_LEVEL)
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    ch.setFormatter(formatter)
    logger.addHandler(ch)

    if args.pseudo_code:
        True
    else:
        True

    lexical_analyser = analex.LexicalAnalyser()

    lineIndex = 0
    for line in f:
        line = line.rstrip('\r\n')
        lexical_analyser.analyse_line(lineIndex, line)
        lineIndex = lineIndex + 1
    f.close()

    # launch the analysis of the program
    lexical_analyser.init_analyser()
    program(lexical_analyser)

    if args.show_ident_table:
        print("------ IDENTIFIER TABLE ------")
        print(str(identifierTable))
        print("------ END OF IDENTIFIER TABLE ------")

    if outputFilename != "":
        try:
            output_file = open(outputFilename, 'w')
        except:
            print("Error: can\'t open output file!")
            return
    else:
        output_file = sys.stdout

    # Outputs the generated code to a file
    instrIndex = 0
    while instrIndex < cg.get_instruction_counter():
        output_file.write("%s\n" % str(
            cg.get_instruction_at_index(instrIndex)[1]))
        instrIndex += 1

    if outputFilename != "":
        output_file.close()

    cg.affiche()


########################################################################


if __name__ == "__main__":
    main()
