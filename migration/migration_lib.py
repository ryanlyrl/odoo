from . import xmlrpc_lib
from xmlrpc.client import Fault

class MigrationLib:

    def __init__(self, from_xmlrpc, to_xmlrpc):
        self.from_odoo = from_xmlrpc
        self.to_odoo = to_xmlrpc
        

    def copy_table(self, from_table, to_table, remove_fields=[]):
        fields_to_remove = ['id', 'write_date']
        fields_to_remove.extend(remove_fields)
        fields_to_remove.extend(self.inspect_differences(from_table)["removed"])
        try:
            for records in self.from_odoo.search_read_paged(from_table, page_size=100):
                records.sort(key=lambda record: record['id'])
                for record in records:
                    print("Migrating record: {}".format(record['name']))
                for record in records:
                    for field in record:
                        if isinstance(record[field], list) and len(record[field]) != 0:
                            record[field] = record[field][0]
                        if 'id' in field:
                            fields_to_remove.append(field)
                    record = MigrationLib.cleanup_data(record, fields_to_remove)

                    try:
                        self.to_odoo.create_record(to_table, record)
                    except Fault as e:
                        print("Migrating record {} failed; Reason: {}".format(record['name'], e))
                        
        except StopIteration: # Probably succeeded if we get through all the records
            print('Finished.')
            return True
        except Exception as e: # Fail on any other exception
            raise e
    

    def inspect_differences(self, table):
        from_db_fields = set(self.from_odoo.get_fields(table))
        to_db_fields = set(self.to_odoo.get_fields(table))

        return {"removed": list(from_db_fields.difference(to_db_fields)), "added": list(to_db_fields.difference(from_db_fields))}


    @staticmethod
    def cleanup_data(record, fields):
        for field in fields:
            if field in record:
                record.pop(field)

        return record