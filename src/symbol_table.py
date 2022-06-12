# Code relatif à la table des identificateurs

import string
from enum import Enum, auto


class SymTableException(Exception):
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return repr(self.value)


class identif:
    def __init__(self, name, type, address):
        self.name = name  # nom de l'identificateur
        self.type = type  # can be procedure, function, boolean or integer
        self.address = address  # adresse de l'identificateur
        self.param = False    # true si la variable est de type "in out"
        self.nb_param = 0     # si l'identificateur est une opération, c'est le nombre de paramètres qu'elle requiert
        self.line = None      # si l'identificateur est une opération, c'est la ligne à laquelle elle est définie
        self.returnType= None   # si l'identificateur est une fonction, c'est le type qu'elle retourne

    def __str__(self):
        return(("Name: "+str(self.name)+"    Type: "+self.type+" Address: "+str(self.address)+"   Param: "+str(self.param)+"  Nb params: "+str(self.nb_param)+"    Line:"+str(self.line)+"    Return type:"+str(self.returnType)))

# classe représentant une liste d'identificateurs d'une portée
class table:

    # Constructeur
    def __init__(self, type):
        self.ident_list = []  # list of every variable within its scope
        self.table_type = type  # can be operation or variable

    ########### Méthodes ###########

    # returns true if the identificator of given name is in the table
    def lookupIdentInTable(self, name):
        for id in self.ident_list:
            if id.name == name:
                return True
        return False

    def setAsParamInTable(self, i):
        self.ident_list[i].param = True

    def insertInTable(self, i: identif):
        if self.table_type != "operation" and i.type in {"procedure", "function"}:
            raise SymTableException(
                "Can't insert an operation in a variable table")
        if self.table_type == "operation" and i.type in {"boolean", "integer"}:
            raise SymTableException(
                "Can't insert a variable in an operation table")
        if self.lookupIdentInTable(i.name):
            raise SymTableException(
                "Can't insert two variables with the same name")
        self.ident_list.append(i)

    def getIdentificatorInTable(self, name):
        for id in self.ident_list:
            if id.name == name:
                return id
        return None  # Maybe raise an exception?

    def getAdInTable(self, name):
        return self.getIdentificatorInTable(name).address

    def getTypeInTable(self, name):
        return self.getIdentificatorInTable(name).type

    def getLine(self, name):
        return self.getIdentificatorInTable(name).line

    def setTypeInTable(self, name, type):
        for id in self.ident_list:
            if id.name == name:
                id.type = type
    # Maybe raise an exception?

    def __str__(self):
        ch = ""
        for id in self.ident_list:
            ch += "\t\t"+str(id)+"\n"
        return("    Type: "+str(self.table_type)+"\n    Symbol Table:\n" + ch)

# Symbol Table declaration
#
# keeps track of semantics of variables i.e. it stores information about the
# scope and binding information about names, information about instances of
# various entities such as variable and function names, classes, objects, etc.
#


class symbol_table:
    # Constructeur
    def __init__(self):
        self.current_scope = 0
        # table where we store operations indentificators
        self.operation_table = table( "operation")
        # table where we store variables, the index corresponds to its scope (0 is the global scope, 1 is the first operation, etc...)
        self.var_tables = [table( "variable")]

    ########### Méthodes ###########

    # returns true if the variable exists in current scope or in global scope
    def lookUpVariable(self, name):
        return (self.var_tables[0].lookupIdentInTable(name) or self.var_tables[self.current_scope].lookupnamedentnamenTable(name))

    # returns true if the operation or procedure exists
    def lookUpOp(self, name):
        return (self.operation_table.lookupIdentInTable(name))

    # returns the identificator
    def getIdent(self, name):
        if self.var_tables[self.current_scope].lookupIdentInTable(name):
            return self.var_tables[self.current_scope].getIdentificatorInTable(name)
        if self.var_tables[0].lookupIdentInTable(name):
            return self.var_tables[0].getIdentificatorInTable(name)
    
    # returns the opeation identificator
    def getOpIdent(self, name):
        return self.operation_table.getIdentificatorInTable(name)

    def insertInCurrentScope(self, name, type):
        # if the variable is not already in the current scope table
        if not self.var_tables[self.current_scope].lookupIdentInTable(name):
            i = identif(name, type, len(
                self.var_tables[self.current_scope].ident_list))
            self.var_tables[self.current_scope].insertInTable(i)
        else:
            raise SymTableException(
                "Variable with same name : "+name+" already declared")

    def insertOp(self, name, type, line):
        if not self.operation_table.lookupIdentInTable(name):
            i = identif(name, type, len(self.operation_table.ident_list))
            i.line = line
            self.operation_table.insertInTable(i)
            self.addTable()
        else:
            raise SymTableException(
                "Variable with same name : "+name+" already declared")

    def nextScope(self):
        self.current_scope += 1

    def addTable(self):
        tab = table("variable")
        self.var_tables.append(tab)

    def setAsParam(self, n):
        for i in range(len(self.var_tables[self.current_scope].ident_list)-1, len(self.var_tables[self.current_scope].ident_list)-n-1, -1):
            self.var_tables[self.current_scope].setAsParamInTable(i)

    def getOpScope(self, name):
        for i in range(len(self.operation_table.ident_list)):
            if self.operation_table.ident_list[i].name == name:
                return i+1

    # return the line, the operation was defined on
    def getOpLine(self, name):
        return self.getOpIdent(name).line

    def getAddress(self, name):
        return self.getIdent(name).address

    def getOpAddress(self, name):
        return self.getOpIdent(name).address
    
    def getOpNbparam(self,name):
        return self.getOpIdent(name).nb_param

    def getType(self, name):
        return self.getIdent(name).type

    def setType(self, name, type):
        self.var_tables[self.current_scope].setTypeInTable(name, type)

    def setNbParam(self, name, n):
        self.getOpIdent(name).nb_param = n

    def setReturnType(self, name, type):
        self.getOpIdent(name).returnType = type

    # returns true if the given identificator name is in the global scope
    def isGlobal(self, name):
        if self.current_scope == 0:
            return self.var_tables[0].lookupIdentInTable(name)
        else:
            return (not self.var_tables[self.current_scope].lookupIdentInTable(name)) and self.var_tables[0].lookupIdentInTable(name)

    def isParam(self, name):
        return self.getIdent(name).param

    def __str__(self):
        ch = ""
        i = 0
        for tab in self.var_tables:
            ch += "Scope "+str(i)+":\n"+str(tab)
            i += 1
        return("Current Scope: " + str(self.current_scope)+"\nOperation table: \n"+str(self.operation_table) + ""+ch)