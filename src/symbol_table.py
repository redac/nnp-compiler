# Code relatif à la table des identificateurs


import string
from enum import Enum,auto

class SymTableException(Exception):
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return repr(self.value)

class TypeIdent(Enum):
    integer=auto()
    boolean=auto()
    function=auto()
    procedure=auto()

class TypeTable(Enum):
    glob=auto()
    loc=auto()
    op=auto()


class identif:
    def __init__(self,name,type,adress):
        self.name=name
        self.type=type # can be procedure, function, boolean or integer
        self.adress=adress
        self.param=False
        self.nbParam=0
        self.line=None

    def __str__(self):
        return("name: "+str(self.name)+"     type: "+self.type+"     adress: "+str(self.adress)+"   Param: "+str(self.param)+"  Nb param: "+str(self.nbParam)+"     line:"+str(self.line))


class table:

    # Constructeur
    def __init__(self,scope,type):
        self.scope=scope
        self.ident_list=[]   #list of every variable within its scope
        self.table_type = type  # can be operation or variable


    ########### Méthodes ###########

    def lookupIdentInTable(self,name):
        for id in self.ident_list:
            if id.name==name:
                return True
        return False

    def setAsParamInTable(self,i):
        self.ident_list[i].param=True

    def insertInTable(self,i:identif):
        if self.table_type!="operation" and i.type in {"procedure","function"}:
            raise SymTableException("Can't insert an operation in a variable table")
        if self.table_type=="operation" and i.type in {"boolean","integer"}:
            raise SymTableException("Can't insert a variable in an operation table")
        if self.lookupIdentInTable(i.name):
            raise SymTableException("Can't insert two variables with the same name")
        self.ident_list.append(i)

    def getIdentificatorInTable(self,name):
        for id in self.ident_list:
            if id.name==name:
                return id
        return None   #### Maybe raise an exception?

    def getAdInTable(self,name):
        return self.getIdentificatorInTable(name).adress
    
    def getTypeInTable(self,name):
        return self.getIdentificatorInTable(name).type

    def getLine(self,name):
        return self.getIdentificatorInTable(name).line

    def setTypeInTable(self,name,type):
        for id in self.ident_list:
            if id.name==name:
                id.type=type
    #### Maybe raise an exception?


    def __str__(self):
        ch=""
        for id in self.ident_list:
            ch+="\t\t"+str(id)+"\n"
        return("\tscope: "+ str(self.scope)+"\n\ttype: "+str(self.table_type)+"\n\tliste des ident:\n" +ch)

class Symbol_table:
    # Constructeur
    def __init__(self):
        self.current_scope=0
        # table where we store operations indentificators
        self.operation_table=table(0,"operation")
        # table where we store variables, the index corresponds to its scope (0 is the global scope, 1 is the first operation call)     
        self.var_tables=[table(0,"variable")]           



    ########### Méthodes ###########

    #returns true if the variable exists in current scope or in global scope
    def lookUpVariable(self,name):
        return (self.var_tables[0].lookupIdentInTable(name) or self.var_tables[self.current_scope].lookupnamedentnamenTable(name))

    # returns true if the operation or procedure exists
    def lookUpOp(self,name):
        return (self.operation_table.lookupIdentInTable(name))

    #returns the identificator
    def getIdent(self,name):
        if self.var_tables[self.current_scope].lookupIdentInTable(name):
            return self.var_tables[self.current_scope].getIdentificatorInTable(name)
        if self.var_tables[0].lookupIdentInTable(name):
            return self.var_tables[0].getIdentificatorInTable(name)

    def getOpIdent(self,name):
        return self.operation_table.getIdentificatorInTable(name)

    # def insertGlobal(self,i:identif):
    #     if not self.var_tables[0].lookupIdentInTable(i):
    #         self.var_tables[0].insertInTable(i)

    def insertInCurrentScope(self,name,type):
        # if the variable is not already in the current scope table
        if not self.var_tables[self.current_scope].lookupIdentInTable(name):
            i=identif(name,type,len(self.var_tables[self.current_scope].ident_list))
            self.var_tables[self.current_scope].insertInTable(i)
        else:
            raise SymTableException("Variable with same name : "+name+" already declared")

    def insertOp(self,name,type,line):
        if not self.operation_table.lookupIdentInTable(name):
            i=identif(name,type,len(self.operation_table.ident_list))
            i.line=line
            self.operation_table.insertInTable(i)
            self.addTable()
        else:
            raise SymTableException("Variable with same name : "+name+" already declared")

    def nextScope(self):
        self.current_scope+=1

    def addTable(self):
        tab=table(self.current_scope,"variable")
        self.var_tables.append(tab)

    def setAsParam(self,n):
        for i in range(len(self.var_tables[self.current_scope].ident_list)-1,len(self.var_tables[self.current_scope].ident_list)-n-1,-1):
            self.var_tables[self.current_scope].setAsParamInTable(i)

    def getOpScope(self,name):
        for i in  range(len(self.operation_table.ident_list)):
            if self.operation_table.ident_list[i].name==name:
                return i+1

    def getOpLine(self,name):
        return self.getOpIdent(name).line

    def getAdress(self,name):
        return self.getIdent(name).adress
    
    def getOpAdress(self,name):
        return self.getOpIdent(name).adress

    def getType(self,name):
        return self.getIdent(name).type

    def setType(self,name,type):
        self.var_tables[self.current_scope].setTypeInTable(name,type)
    
    def setNbParam(self,name,n):
        self.getOpIdent(name).nbParam=n

    def isGlobal(self,name):
        if self.current_scope==0:
            return self.var_tables[0].lookupIdentInTable(name)
        else:
            return (not self.var_tables[self.current_scope].lookupIdentInTable(name)) and self.var_tables[0].lookupIdentInTable(name)

    # def setAsParam(self,name):
    #     self.var_tables[self.current_scope].setAsParamInTable(name)

    def isParam(self,name):
        return self.getIdent(name).param

    def __str__(self):
        ch=""
        i=0
        for tab in self.var_tables:
            ch+="scope "+str(i)+":\n"+str(tab)+"\n"
            i+=1
        return("current scope: "+ str(self.current_scope)+"     \noperation table: \n"+str(self.operation_table) +""+ch)


# # tab1=table(1,"variable")
# id1=identif("sum","integer",0)
# # tab1.insertInTable(id1)
# id2=identif("bool1","boolean",1)
# # tab1.insertInTable(id2)
# id3=identif("x","integer",1)
# # tab1.insertInTable(id3)
# tab1=table(1,"variable")

# id_table=Symbol_table()
# id_table.insertInCurrentScope("sum","integer")
# id_table.insertInCurrentScope("f","boolean")
# id_table.insertOp("g","function")
# id_table.insertOp("h","function")
# id_table.insertOp("i","function")
# id_table.insertOp("f","function")
# id_table.nextScope()
# id_table.insertInCurrentScope("sum","integer")
# id_table.insertInCurrentScope("x","integer")

# id_table.setAsParam(2)

# # id1=id_table.getIdent("sum")
# ad1=id_table.getOpAdress("f")

# print(id_table)
# print(str(id_table.getOpScope("f")))
# # print(ad1)
# # print("is param?: "+str(id_table.isParam("sum")))
