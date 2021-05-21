'''
ORM wrapper for Odoo (specifically 13, but way work with other versions)
Intended for use for database migration

Written for Toys on Fire by Ryan Ly (2020)
'''

class ORM:

    def __init__(self, odoo, db):
        '''
        Initialize the ORM class

        The Odoo is 
        '''
        self.odoo = odoo
        self.registry = odoo.registry(db)
        self.cr = self.registry.cursor()
        self.uid = odoo.SUPERUSER_ID
        self.env = odoo.api.Environment(self.cr, self.uid, context={})

    
    def run(self):
        pass

    
    def search(self, table, domain=[]):
        return self.env[table].search(domain)

    
    def create(self, table, vals):
        return self.env[table].create(vals)

    
    def clear_table(self, table):
        return self.search(table).unlink()

    def get_fields(self, table):
        return self.env[table].fields_get().keys()

    def write(self, table, id, vals):
        return self.env[table].browse(id).write(vals)

    @staticmethod
    def rename_fields(self, data, name_map):
        for field in name_map:
            if field in data:
                data[name_map[field]] = data[field]
                data.pop(field)
        return data


    @staticmethod
    def remove_field(self, data, field):
        if field in data:
            data.pop(field)
        return data
