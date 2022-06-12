#!/usr/bin/python

# @package anasyn
# Syntactical Analyser package.
#

from glob import glob
from statistics import variance
import sys
import argparse
import re
import logging


import analex
import codeGenerator
from symbol_table import symbol_table

logger = logging.getLogger('anasyn')

DEBUG = True
LOGGING_LEVEL = logging.DEBUG


identifierTable = {}
anyVarsIDs = []    # Stores variables with unknown type
identifier_table = symbol_table()
Proc_call = None


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
    cg.addCode("tra(ad1);")
    corpsProgPrinc(lexical_analyser)


def specifProgPrinc(lexical_analyser):
    # Intentionally not adding the first procedure to the symbol table
    lexical_analyser.acceptKeyword("procedure")
    ident = lexical_analyser.acceptIdentifier()
    logger.debug("Name of program : "+ident)


def corpsProgPrinc(lexical_analyser):
    if not lexical_analyser.isKeyword("begin"):
        logger.debug("Parsing declarations")
        partieDecla(lexical_analyser)
        logger.debug("End of declarations")
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
        cg.set_instruction_at_index(
            1, "tra("+str(cg.get_instruction_counter())+")")
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
    identifier_table.insertOp(ident, "procedure", cg.get_instruction_counter())
    identifier_table.current_scope = identifier_table.getOpScope(ident)
    logger.debug("Name of procedure : "+ident)
    n = partieFormelle(lexical_analyser)
    identifier_table.setNbParam(ident, n)
    lexical_analyser.acceptKeyword("is")
    corpsProc(lexical_analyser)
    cg.addCode("retourProc()")
    identifier_table.current_scope = 0


def fonction(lexical_analyser):
    lexical_analyser.acceptKeyword("function")
    ident = lexical_analyser.acceptIdentifier()
    identifier_table.insertOp(ident, "function", cg.get_instruction_counter())
    logger.debug("Name of function : "+ident)
    identifier_table.current_scope = identifier_table.getOpScope(ident)
    n = partieFormelle(lexical_analyser)
    identifier_table.setNbParam(ident, n)
    lexical_analyser.acceptKeyword("return")
    type=nnpType(lexical_analyser)
    identifier_table.setReturnType(ident, type)
    lexical_analyser.acceptKeyword("is")
    corpsFonct(lexical_analyser)
    identifier_table.current_scope = 0


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
    n = 0
    if not lexical_analyser.isCharacter(")"):
        n = listeSpecifFormelles(lexical_analyser)
    lexical_analyser.acceptCharacter(")")
    return n


def listeSpecifFormelles(lexical_analyser):
    n = specif(lexical_analyser)
    n2=0
    if not lexical_analyser.isCharacter(")"):
        lexical_analyser.acceptCharacter(";")
        n2=listeSpecifFormelles(lexical_analyser)
    return n+n2


def specif(lexical_analyser):
    n = listeIdent(lexical_analyser)
    io = ""
    lexical_analyser.acceptCharacter(":")
    if lexical_analyser.isKeyword("in"):
        io = mode(lexical_analyser)
    if io == "in out":
        identifier_table.setAsParam(n)
    nnpType(lexical_analyser)
    return n


def mode(lexical_analyser):
    lexical_analyser.acceptKeyword("in")
    if lexical_analyser.isKeyword("out"):
        lexical_analyser.acceptKeyword("out")
        logger.debug("in out parameter")
        return "in out"
    else:
        logger.debug("in parameter")
        return "in"


def nnpType(lexical_analyser):
    # Parses types
    for obj in identifier_table.var_tables[identifier_table.current_scope].ident_list:
        objType = obj.type
        if objType == "any":
            anyVarsIDs.append(obj.name)
    if lexical_analyser.isKeyword("integer"):
        lexical_analyser.acceptKeyword("integer")
        logger.debug("integer type")
        for varID in anyVarsIDs:
            # identifierTable[varID][1] = "integer"
            identifier_table.setType(varID, "integer")
        anyVarsIDs[:] = []
        return "integer"
    elif lexical_analyser.isKeyword("boolean"):
        lexical_analyser.acceptKeyword("boolean")
        for varID in anyVarsIDs:
            # identifierTable[varID][1] = "boolean"
            identifier_table.setType(varID, "boolean")
            # anyVarsIDs.remove(varID)
        anyVarsIDs[:] = []
        logger.debug("boolean type")
        return "boolean"
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
    cg.addCode("reserver("+str(n)+")")
    lexical_analyser.acceptCharacter(";")

# La fonction renvoie le nombre d'éléments de la liste de déclaration


def listeIdent(lexical_analyser):
    n = 1
    ident = lexical_analyser.acceptIdentifier()
    logger.debug("identifier found: "+str(ident))
    # Add variable to the ident table, with an "any" type for now
    # identifierTable[id(str(ident))] = [ident, "any", len(identifierTable), []]
    identifier_table.insertInCurrentScope(ident, "any")

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
            addr = identifier_table.getAddress(ident)
            t1 = identifier_table.getType(ident)
            if identifier_table.isGlobal(ident):
                cg.addCode("empiler("+str(addr)+")")
            elif identifier_table.isParam(ident):
                cg.addCode("empilerParam("+str(addr)+")")
            else:
                cg.addCode("empilerAd("+str(addr)+")")
            lexical_analyser.acceptSymbol(":=")
            t2 = expression(lexical_analyser)
            if t1 != t2:
                raise AnaSynException(
                    "TypeError: := requires 2 arguments of same type")
            cg.addCode("affectation()")
            logger.debug("parsed affectation")
        elif lexical_analyser.isCharacter("("):
            cg.addCode("reserverBloc()")
            lexical_analyser.acceptCharacter("(")
            nbParam = 0
            global Proc_call
            Proc_call = [ident, -1]
            if not lexical_analyser.isCharacter(")"):
                nbParam = listePe(lexical_analyser, 0)+1
            if nbParam!=identifier_table.getOpNbparam(ident):
                raise AnaSynException("Not the good amount of parameters: procedure "+ident+" expected "+str(identifier_table.getOpNbparam(ident))+" arguments, but was given "+str(nbParam))
            lexical_analyser.acceptCharacter(")")
            logger.debug("parsed procedure call")
            line = identifier_table.getOpLine(ident)
            cg.addCode("traStat("+str(line-1)+","+str(nbParam)+")")
            Proc_call = None
        else:
            logger.error("Expecting procedure call or affectation!")
            raise AnaSynException("Expecting procedure call or affectation!")

    else:
        logger.error("Unknown Instruction <" +
                     lexical_analyser.get_value() + ">!")
        raise AnaSynException("Unknown Instruction <" +
                              lexical_analyser.get_value() + ">!")


def listePe(lexical_analyser, n):
    global Proc_call
    if Proc_call != None:
        a = Proc_call[1]
        a += 1
        Proc_call[1] = a
    expression(lexical_analyser)
    if lexical_analyser.isCharacter(","):
        lexical_analyser.acceptCharacter(",")
        return listePe(lexical_analyser, n+1)
    return n


def expression(lexical_analyser):
    logger.debug("parsing expression: " + str(lexical_analyser.get_value()))
    t1 = exp1(lexical_analyser)
    if lexical_analyser.isKeyword("or"):
        lexical_analyser.acceptKeyword("or")
        t2 = exp1(lexical_analyser)
        cg.addCode("ou()")
        # type check
        if t1 != "boolean" or t2 != "boolean":
            raise AnaSynException("TypeError: ou requires booleans")
    return t1


def exp1(lexical_analyser):
    logger.debug("parsing exp1")
    t1 = exp2(lexical_analyser)
    if lexical_analyser.isKeyword("and"):
        lexical_analyser.acceptKeyword("and")
        t2 = exp2(lexical_analyser)
        # type check
        if t1 != "boolean" or t2 != "boolean":
            raise AnaSynException("TypeError: et requires booleans")
        cg.addCode("et()")
    return t1


def exp2(lexical_analyser):
    logger.debug("parsing exp2")
    t1 = exp3(lexical_analyser)
    if lexical_analyser.isSymbol("<") or \
            lexical_analyser.isSymbol("<=") or \
            lexical_analyser.isSymbol(">") or \
            lexical_analyser.isSymbol(">="):
        infeg = lexical_analyser.isSymbol("<=")
        inf = lexical_analyser.isSymbol("<")
        sup = lexical_analyser.isSymbol(">")
        opRel(lexical_analyser)
        t2 = exp3(lexical_analyser)
        # type check
        if t1 != "integer" or t2 != "integer":
            if infeg:
                raise AnaSynException("TypeError: <= requires integers")
            elif inf:
                raise AnaSynException("TypeError: < requires integers")
            elif sup:
                raise AnaSynException("TypeError: > requires integers")
            else:
                raise AnaSynException("TypeError: >= requires integers")
        if infeg:
            cg.addCode("infeg()")
        elif inf:
            cg.addCode("inf()")
        elif sup:
            cg.addCode("sup()")
        else:
            cg.addCode("supeg()")
        return "boolean"
    elif lexical_analyser.isSymbol("=") or \
            lexical_analyser.isSymbol("/="):
        egal = lexical_analyser.isSymbol("=")
        opRel(lexical_analyser)
        t2 = exp3(lexical_analyser)
        # type check
        if t1 != t2:
            if egal:
                raise AnaSynException(
                    "TypeError: = requires 2 arguments of same type")
            else:
                raise AnaSynException(
                    "TypeError: /= requires 2 arguments of same type")
        if egal:
            cg.addCode("egal()")
        else:
            cg.addCode("diff()")
        return "boolean"
    return t1


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
    t1 = exp4(lexical_analyser)
    if lexical_analyser.isCharacter("+") or lexical_analyser.isCharacter("-"):
        moins = lexical_analyser.isCharacter("-")
        opAdd(lexical_analyser)
        t2 = exp4(lexical_analyser)
        # type check
        if t1 != "integer" or t2 != "integer":
            if moins:
                raise AnaSynException("TypeError: sous() requires integers")
            else:
                raise AnaSynException("TypeError: add() requires integers")
        if moins:
            cg.addCode("sous()")
        else:
            cg.addCode("add()")
    return t1


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
    t1 = prim(lexical_analyser)
    if lexical_analyser.isCharacter("*") or lexical_analyser.isCharacter("/"):
        fois = lexical_analyser.isCharacter("*")
        opMult(lexical_analyser)
        t2 = prim(lexical_analyser)
        # type check
        if t1 != "integer" or t2 != "integer":
            if fois:
                raise AnaSynException("TypeError: mult() requires integers")
            else:
                raise AnaSynException("TypeError: div() requires integers")
        if fois:
            cg.addCode("mult()")
        else:
            cg.addCode("div()")
    return t1


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
    plus = False
    t1 = None
    if lexical_analyser.isCharacter("+") or lexical_analyser.isCharacter("-") or lexical_analyser.isKeyword("not"):
        moins = lexical_analyser.isCharacter("-")
        non = lexical_analyser.isKeyword("not")
        plus = lexical_analyser.isCharacter("+")
        a = lexical_analyser.get_value()
        t1 = opUnaire(lexical_analyser)
    t2 = elemPrim(lexical_analyser)
    if t1 != t2:
        if non:
            raise AnaSynException("TypeError: non() requires a boolean")
        elif moins:
            raise AnaSynException("TypeError: moins() requires an integer")
        elif plus:
            raise AnaSynException("TypeError: plus() require an integer")
    elif non:
        cg.addCode("non()")
    elif moins:
        cg.addCode("moins()")
    return t2


def opUnaire(lexical_analyser):
    logger.debug("parsing unary operator: " + lexical_analyser.get_value())
    if lexical_analyser.isCharacter("+"):
        lexical_analyser.acceptCharacter("+")
        return "integer"

    elif lexical_analyser.isCharacter("-"):
        lexical_analyser.acceptCharacter("-")
        return "integer"

    elif lexical_analyser.isKeyword("not"):
        lexical_analyser.acceptKeyword("not")
        return "boolean"

    else:
        msg = "Unknown additive operator <" + lexical_analyser.get_value() + ">!"
        logger.error(msg)
        raise AnaSynException(msg)


def elemPrim(lexical_analyser):
    logger.debug("parsing elemPrim: " + str(lexical_analyser.get_value()))
    if lexical_analyser.isCharacter("("):
        lexical_analyser.acceptCharacter("(")
        type = expression(lexical_analyser)
        lexical_analyser.acceptCharacter(")")
        return type
    elif lexical_analyser.isInteger() or lexical_analyser.isKeyword("true") or lexical_analyser.isKeyword("false"):
        return valeur(lexical_analyser)
    elif lexical_analyser.isIdentifier():
        ident = lexical_analyser.acceptIdentifier()
        type = None
        if lexical_analyser.isCharacter("("):			# Appel fonct
            line = identifier_table.getOpLine(ident)
            cg.addCode("reserverBloc()")
            lexical_analyser.acceptCharacter("(")
            nbParam = 0
            if not lexical_analyser.isCharacter(")"):
                nbParam = listePe(lexical_analyser, 0)+1
            lexical_analyser.acceptCharacter(")")
            if nbParam!=identifier_table.getOpNbparam(ident):
                raise AnaSynException("Not the good amount of parameters: function "+ident+" expected "+str(identifier_table.getOpNbparam(ident))+" arguments, but was given "+str(nbParam))
            cg.addCode("traStat("+str(line-1)+","+str(nbParam)+")")
            logger.debug("parsed procedure call")
            logger.debug("Call to function: " + ident)
            return identifier_table.getOpIdent(ident).returnType
        else:
            addr = identifier_table.getAddress(ident)
            type = identifier_table.getType(ident)
            if identifier_table.isGlobal(ident):
                cg.addCode("empiler("+str(addr)+")")
            elif identifier_table.isParam(ident):
                cg.addCode("empilerParam("+str(addr)+")")
            else:
                cg.addCode("empilerAd("+str(addr)+")")
            global Proc_call
            if Proc_call == None:
                cg.addCode("valeurPile()")
            else:
                num_var = Proc_call[1]
                nom_Proc = Proc_call[0]
                nom_var = identifier_table.var_tables[identifier_table.getOpScope(
                    nom_Proc)].ident_list[num_var].name
                if not identifier_table.var_tables[identifier_table.getOpScope(nom_Proc)].getIdentificatorInTable(nom_var).param:
                    cg.addCode("valeurPile()")
            logger.debug("Use of an identifier as an expression: " + ident)
        return type
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
        type = None
        # for ide in identifierTable:
        #         if ident==identifierTable[ide][0]:
        #             addr=identifierTable[ide][2]
        addr = identifier_table.getAddress(ident)
        type = identifier_table.getType(ident)
        # type check
        if type != "integer":
            raise AnaSynException("TypeError: get() requires an integer")
        if identifier_table.isGlobal(ident):
            cg.addCode("empiler("+str(addr)+")")
        elif identifier_table.isParam(ident):
            cg.addCode("empilerParam("+str(addr)+")")
        else:
            cg.addCode("empilerAd("+str(addr)+")")
        cg.addCode("get()")
        lexical_analyser.acceptCharacter(")")
        logger.debug("Call to get "+ident)
    elif lexical_analyser.isKeyword("put"):
        lexical_analyser.acceptKeyword("put")
        lexical_analyser.acceptCharacter("(")
        ident = lexical_analyser.get_value()
        type = expression(lexical_analyser)
        # type check
        if type != "integer":
            raise AnaSynException("TypeError: put() requires an integer")
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
    type=expression(lexical_analyser)
    if type!="boolean":
        raise AnaSynException("TypeError: while requires a boolean")
    lexical_analyser.acceptKeyword("loop")
    cg.addCode("tze(ad2); //doit pas apparaitre, remplacer avec ad2")
    index_ad2 = cg.get_instruction_counter()-1
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
    t = expression(lexical_analyser)
    if t != "boolean":
        raise AnaSynException("TypeError: if requires a boolean")

    lexical_analyser.acceptKeyword("then")
    # modifier ad1 pour avoir la bonne addresse
    index_ad1 = cg.get_instruction_counter()
    cg.addCode("tze(ad1); //ne doit pas apparaitre")
    suiteInstr(lexical_analyser)
    index_ad2 = None

    if lexical_analyser.isKeyword("else"):
        lexical_analyser.acceptKeyword("else")
        index_ad2 = cg.get_instruction_counter()
        cg.addCode("tra(ad2); //ne doit pas apparaitre")
        ad1 = cg.get_instruction_counter()
        cg.set_instruction_at_index(index_ad1, "tze("+str(ad1)+"); //else")
        suiteInstr(lexical_analyser)

    lexical_analyser.acceptKeyword("end")
    ad2 = cg.get_instruction_counter()
    instr = "tra"
    if index_ad2 == None:  # Si if sans else
        index_ad2 = index_ad1
        instr = "tze"
    cg.set_instruction_at_index(index_ad2, instr+"("+str(ad2)+"); // if")
    logger.debug("end of if")


def retour(lexical_analyser):
    logger.debug("parsing return instruction")
    lexical_analyser.acceptKeyword("return")
    expression(lexical_analyser)
    cg.addCode("retourFonc()")

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
        print(str(identifier_table))
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
            cg.get_instruction_at_index(instrIndex)))
        instrIndex += 1

    if outputFilename != "":
        output_file.close()


########################################################################


if __name__ == "__main__":
    main()