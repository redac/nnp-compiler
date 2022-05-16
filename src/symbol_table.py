# Code relatif à la table des identificateurs
#
# Symbol Table declaration
#
# keeps track of semantics of variables i.e. it stores information about the
# scope and binding information about names, information about instances of
# various entities such as variable and function names, classes, objects, etc.
#
# key = object identity (unique) by calling the python function id
# table[id] = ['ident', 'type', @address, [[(if function) param1, param2, ...)],returnType]]

import string


class symbol_table:

    # Constructeur
    def __init__(self):
        self.table = {}
        self.any_vars_ids = []  # Stores variables with unknown type
        self.object_index = 0

    ########### Méthodes ###########

    def add_ident(self, ident: string, type: string):
        self.table[id(ident)] = [ident, type, len(self.table), [[]]]
        self.object_index += 1

    def get_address(self, ident):
        return self.table[id(ident)][2]

    def get_type(self, ident):
        return self.table[id(ident)][1]

    def get_return_types(self, ident):
        return self.table[id(ident)][3]
