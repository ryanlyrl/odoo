import xmlrpc.client
from .xmlrpc_lib import XmlrpcLib 
from .migration_lib import MigrationLib
from pprint import pprint
from .orm import ORM
import traceback

def run(odoo, table):
    # odoo11 = XmlrpcLib('http://192.168.1.5:8071', '11_test', 'test@test.com', 'test')
    # odoo13 = XmlrpcLib('http://192.168.1.5:8070', '13_test', 'test1@test.com', 'test')

    # print(odoo11.get_version())
    # print(odoo13.get_version())

    # migrate = MigrationLib(odoo11, odoo13)
    # pprint('Odoo 11: {}'.format(odoo11.search_read('res.users')))

    odoo8 = XmlrpcLib('http://192.168.1.5:8069', 'tof8', 'ryanly.rl1@gmail.com', 'tofpro!')
    odoo13 = XmlrpcLib('http://192.168.1.5:8070', 'migration-test-2020-08-16', 'test@test.com', 'test')
    migrate = MigrationLib(odoo8, odoo13)
    diff = migrate.inspect_differences(table)
    orm = ORM(odoo, 'migration-test-2020-08-16')
    print(diff)
    migrated_ids = []
    try:
        for records in odoo8.search_read_paged(table, page_size=100):
            records.sort(key=lambda record: record['id'])
            for record in records:
                for field in record:
                    if isinstance(record[field], list) and len(record[field]) != 0 and not 'ids' in field and 'id' in field:
                        record[field] = record[field][0]
                for field in diff['removed']:
                    record.pop(field, None)
                for field in list(record.keys()):
                    if not record[field]:
                        record.pop(field, None)
                    if 'ids' in field:
                        record.pop(field, None)
                record.pop('user_id', None)
                record.pop('currency_id', None)

                if record['id'] and record['id'] not in migrated_ids:
                    print("Migrating record: {}".format(record['name']))
                    migrated_ids.append(record['id'])
                    try:
                        orm.create(table, record)
                    except Exception as e:
                        print("Migrating record {} failed; Reason: {}".format(record['name'], e))
                        print(record)
                        traceback.print_exc()
                        print(migrated_ids)
                        input("Press any key to continue...")
                    
    except StopIteration: # Probably succeeded if we get through all the records
        print('Finished.')
        return True
    except Exception as e: # Fail on any other exception
        raise e
    
    while True:
        check = input("Copying complete. Commit? (Y/N)")
        if check.lower() == 'y':
            orm.cr.commit()
            break
        elif check.lower() == 'n':
            break

    orm.cr.close()