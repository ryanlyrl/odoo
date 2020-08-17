from orm import ORM
from xmlrpc_lib import XmlrpcLib
import getpass

URL = 'http://192.168.1.5:8069'
#USERNAME = input("Old DB username: ")
#PASSWORD = getpass.getpass(prompt="Old DB password: ")
USERNAME = 'ryanly.rl1@gmail.com'
PASSWORD = 'tofpro1!'


def run(odoo, old_table, new_table, olddb, newdb, field_changes={}):
    new = ORM(odoo, newdb)
    old = XmlrpcLib(URL, olddb, USERNAME, PASSWORD)

    new_fields = new.get_fields(new_table)
    for records in old.search_read_paged(old_table, page_size=100):
        for record in records:
            # for field in field_changes.get('remove', {}):
            #     record.pop(field)
            # for field in field_changes.get('rename', {}):
            #     record[field[1]] = record.pop(field[0])
            new_rec = {}
            for field in record:
                if field in new_fields:
                    new_rec[field] = record[field]
            new_rec = ORM.cleanup(new_rec)
            if 'remove' in field_changes:
                for field in field_changes['remove']:
                    new_rec = ORM.remove_field(new_rec, field)
            print("Migration record: {}".format(new_rec['id']))
            if new_rec['id'] in [1,2,3,4,5,6]:
                continue
            new.create(new_table, new_rec)
            print("Migration finished")
    new.cr.commit()
    print("Commiting changes")
    new.cr.close()
