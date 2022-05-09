# Code relatif à la table des identificateurs


import string


class symbol_table:

    # Constructeur
    def __init__(self):
        self.table = {}
        self.object_index = 0

    ########### Méthodes ###########

    def add_ident(self, ident: string, type: string):
        self.table[id(ident)] = [ident, type, len(self.table), []]
        self.object_index += 1

    def get_address(self, ident):
        return self.table[id(ident)][2]

    def get_type(self, ident):
        return self.table[id(ident)][1]

    def get_return_types(self, ident):
        return self.table[id(ident)][3]
