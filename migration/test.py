import xmlrpc.client
from .xmlrpc_lib import XmlrpcLib 
from .migration_lib import MigrationLib
from pprint import pprint
from .orm import ORM
import traceback
from psycopg2 import IntegrityError
import re
import unidecode

STOP_ON_ERROR = False
FILENAME = 'migrations.txt'
ODOO_8 = {
    'username': 'ryanly.rl1@gmail.com',
    'password': 'tofpro!',
    'ip': 'http://192.168.1.5:8069',
    'db': 'tof8'
}
ODOO_13 = {
    'username': 'admin@toysonfire.ca',
    'password': 'test',
    'ip': 'http://192.168.1.5:8070',
    'db': 'odoo13-migrated-2021-05-17'
}


'''
Commands list:
copy [table_name]
copy [table_name] [column]
'''
# def run(odoo, filename=FILENAME):
#     with open(filename, 'r') as file:
#         commands = file.readlines()
#     commands = [line.strip() for line in commands]
#     for command in commands:
#         tokens = command.split(' ')
#         if tokens[0] == 'copy':
#             if len(tokens) == 2:
#                 copy_table(odoo, tokens[1])
#             elif len(tokens) == 3:
#                 copy_column(odoo, tokens[1], tokens[2])

def run(odoo):
    # Copy all tables, then fix countries
    copy_table(odoo, 'res.country.state')
    copy_table(odoo, 'res.partner')
    copy_table(odoo, 'mail.alias')
    copy_table(odoo, 'res.users')
    copy_table(odoo, 'product.category')
    copy_table(odoo, 'product.template')
    fixCountries(odoo)
    copy_extra_images(odoo)

def copy_table(odoo, table):
    # odoo11 = XmlrpcLib('http://192.168.1.5:8071', '11_test', 'test@test.com', 'test')
    # odoo13 = XmlrpcLib('http://192.168.1.5:8070', '13_test', 'test1@test.com', 'test')

    # print(odoo11.get_version())
    # print(odoo13.get_version())

    # migrate = MigrationLib(odoo11, odoo13)
    # pprint('Odoo 11: {}'.format(odoo11.search_read('res.users')))

    odoo8 = XmlrpcLib(ODOO_8['ip'], ODOO_8['db'], ODOO_8['username'], ODOO_8['password'])
    odoo13 = XmlrpcLib(ODOO_13['ip'], ODOO_13['db'], ODOO_13['username'], ODOO_13['password'])
    migrate = MigrationLib(odoo8, odoo13)
    diff = migrate.inspect_differences(table)
    orm = ORM(odoo, ODOO_13['db'])
    migrated_ids = []
    error_ids = []
    items_copied = 0
    num_items = odoo8.count_records(table)
    print('Migrating table {}...'.format(table))
    printProgressBar(0, num_items, prefix = 'Progress:', length = 50)
    try:
        for records in odoo8.search_read_paged(table, page_size=100):
            records.sort(key=lambda record: record['id'])
            for record in records:
                for field in record:
                    if isinstance(record[field], list) and len(record[field]) != 0 and not 'ids' in field and 'id' in field:
                        record[field] = record[field][0]
                    elif isinstance(record[field], bool):
                        record[field] = int(record[field])
                for field in list(record.keys()):
                    if not record[field]:
                        record.pop(field, None)
                    # TODO: these are probably relational fields that need to be converted to the [(6, 0, ids)] format
                    if 'ids' in field:
                        record.pop(field, None)
                record.pop('user_id', None)
                record.pop('currency_id', None)

                if table == 'res.partner':
                    record.pop('parent_id', None) # We're removing parent IDs for res_partner since it's not non-null, we need to put them back after we migrate the other tables
                    record.pop('commercial_partner_id', None)

                    for field in ['supplier', 'customer']:
                        if field in record:
                            record[field + '_rank'] = int(record[field])
                
                if table == 'res.users':
                    record.pop('groups_id', None)

                if table == 'product.category':
                    record.pop('parent_id', None)

                if table == 'product.template':
                    for field in ['taxes_id', 'supplier_taxes_id', 'category_id']:
                        if field in record and isinstance(record[field], int):
                            record[field] = [(6, 0, [record[field]])]

                    for field in ['frontpagetags']:
                        if field in record:
                            record[field] = record[field][0]

                    for field in ['manufacturer']:
                        if field in record and isinstance(record[field], list) and len(record[field]) != 0:
                            if isinstance(record[field][0], list):
                                record[field] = [(6, 0, [item[0] for item in record[field]])]
                            else:
                                record[field] = [(6, 0, [record[field][0]])]

                    # Convert timestamp into date by removing time
                    for field in ['new_until_date', 'preorder_release_date']:
                        if field in record:
                            record[field] = record[field].split()[0]

                    # Rename images
                    record['image_1920'] = record['image']
                    
                if table == 'product.category':
                    record.pop('child_id', None)

                # Remove any extraneous fields
                for field in diff['removed']:
                    record.pop(field, None)

                if record['id'] and record['id'] not in migrated_ids:
                    # print("Migrating record: {}".format(record['name']))
                    try:
                        orm.create(table, record)
                        migrated_ids.append(record['id'])
                        if STOP_ON_ERROR:
                            input('Success.')
                        orm.cr.commit()
                    except Exception as e:
                        error_ids.append(record['id'])
                        orm.cr.rollback()
                        if STOP_ON_ERROR:
                            print("Migrating record {} failed; Reason: {}".format(record['name'], e))
                            print(record)
                            traceback.print_exc()
                            input("Press any key to continue...")

                items_copied += 1
                printProgressBar(items_copied, num_items, prefix = 'Progress:', length = 50, success=len(migrated_ids), failure=len(error_ids))

                    
    except StopIteration: # Probably succeeded if we get through all the records
        print('Finished.')
        return True
    except Exception as e: # Fail on any other exception
        raise e
    
    # while True:
    print('{} records were migrated.'.format(len(migrated_ids)))
    print('{} records failed to migrate.'.format(len(error_ids)))
    check = input("Copying complete. Press any key to continute.")
    # if check.lower() == 'y':
    #     orm.cr.commit()
    #     break
    # elif check.lower() == 'n':
    #     orm.cr.rollback()
    #     break

    orm.cr.close()

def copy_extra_images(odoo):
    table = 'extra.image'

    odoo8 = XmlrpcLib(ODOO_8['ip'], ODOO_8['db'], ODOO_8['username'], ODOO_8['password'])
    odoo13 = XmlrpcLib(ODOO_13['ip'], ODOO_13['db'], ODOO_13['username'], ODOO_13['password'])
    migrate = MigrationLib(odoo8, odoo13)
    orm = ORM(odoo, ODOO_13['db'])
    migrated_ids = []
    error_ids = []
    items_copied = 0
    num_items = odoo8.count_records(table)
    print('Migrating table {}...'.format(table))
    printProgressBar(0, num_items, prefix = 'Progress:', length = 50)

    try:
        for records in odoo8.search_read_paged(table, page_size=100):
            records.sort(key=lambda record: record['id'])
            for record in records:
                try:
                    name = record['image_name'] or ''
                    tmpl_id = record['template_id'][0]
                    image = record['product_image']
                    print(tmpl_id, name)
                    orm.write('product.template', tmpl_id, {'product_template_image_ids': [(0, 0, {'name': name, 'image_1920': image})]})
                    migrated_ids.append(record['id'])
                    if STOP_ON_ERROR:
                        input('Success.')
                    orm.cr.commit()
                except Exception as e:
                    error_ids.append(record['id'])
                    orm.cr.rollback()
                    if STOP_ON_ERROR:
                        print("Migrating record {} failed; Reason: {}".format(record['name'], e))
                        print(record)
                        traceback.print_exc()
                        input("Press any key to continue...")

                items_copied += 1
                printProgressBar(items_copied, num_items, prefix = 'Progress:', length = 50, success=len(migrated_ids), failure=len(error_ids))
    except StopIteration: # Probably succeeded if we get through all the records
        print('Finished.')
        return True
    except Exception as e: # Fail on any other exception
        raise e

def copy_column(odoo, table, column, new_name=''):
    odoo8 = XmlrpcLib(ODOO_8['ip'], ODOO_8['db'], ODOO_8['username'], ODOO_8['password'])
    odoo13 = XmlrpcLib(ODOO_13['ip'], ODOO_13['db'], ODOO_13['username'], ODOO_13['password'])
    migrate = MigrationLib(odoo8, odoo13)
    diff = migrate.inspect_differences(table)
    orm = ORM(odoo, ODOO_13['db'])
    migrated_ids = []
    error_ids = []
    items_copied = 0
    num_items = odoo8.count_records(table)
    print('Copying column {} in table {}'.format(column, table))
    printProgressBar(0, num_items, prefix = 'Progress:', length = 50)
    name = new_name or column # If no new name is given, reuse the old one
    try:
        for records in odoo8.search_read_paged(table, page_size=100):
            records.sort(key=lambda record: record['id'])
            for record in records:                  
                if 'id' in record and column in record:
                    try:
                        orm.write(table, record['id'], {name: record[column]})
                        migrated_ids.append(record['id'])
                        if STOP_ON_ERROR:
                            input('Success.')
                        orm.cr.commit()
                    except IntegrityError as e:
                        pass
                    except Exception as e:
                        error_ids.append(record['id'])
                        orm.cr.rollback()
                        if STOP_ON_ERROR:
                            print("Migrating record {} failed; Reason: {}".format(record['name'], e))
                            traceback.print_exc()
                            input("Press any key to continue...")

                items_copied += 1
                printProgressBar(items_copied, num_items, prefix = 'Progress:', length = 50, success=len(migrated_ids), failure=len(error_ids))

                    
    except StopIteration: # Probably succeeded if we get through all the records
        print('Finished.')
    except Exception as e: # Fail on any other exception
        raise e
    
    # while True:
    print('{} records were migrated.'.format(len(migrated_ids)))
    print('{} records failed to migrate.'.format(len(error_ids)))
    check = input("Copying complete. Press any key to continute.")
    # if check.lower() == 'y':
    #     orm.cr.commit()
    #     break
    # elif check.lower() == 'n':
    #     orm.cr.rollback()
    #     break

    orm.cr.close()

# https://stackoverflow.com/questions/3173320/text-progress-bar-in-the-console
# Print iterations progress
def printProgressBar (iteration, total, prefix = '', suffix = '', decimals = 1, length = 100, fill = '█', printEnd = "\r", success=0, failure=0):
    """
    Call in a loop to create terminal progress bar
    @params:
        iteration   - Required  : current iteration (Int)
        total       - Required  : total iterations (Int)
        prefix      - Optional  : prefix string (Str)
        suffix      - Optional  : suffix string (Str)
        decimals    - Optional  : positive number of decimals in percent complete (Int)
        length      - Optional  : character length of bar (Int)
        fill        - Optional  : bar fill character (Str)
        printEnd    - Optional  : end character (e.g. "\r", "\r\n") (Str)
    """
    percent = ("{0:." + str(decimals) + "f}").format(100 * (iteration / float(total)))
    filledLength = int(length * iteration // total)
    bar = fill * filledLength + '-' * (length - filledLength)
    print(f'\r{prefix} |{bar}| {iteration}/{total} - {percent}% {suffix} - Success: {success} Failure: {failure}', end = printEnd)
    # Print New Line on Complete
    if iteration == total: 
        print()

def fixCountries(odoo):
    odoo8 = XmlrpcLib(ODOO_8['ip'], ODOO_8['db'], ODOO_8['username'], ODOO_8['password'])
    odoo13 = XmlrpcLib(ODOO_13['ip'], ODOO_13['db'], ODOO_13['username'], ODOO_13['password'])
    orm = ORM(odoo, ODOO_13['db'])
    odoo13_countries = {} # name: id
    odoo8_countries = {} # id: name

    odoo13_states = {} # name: id
    odoo8_states = {} # id: name
    count = 0
    migrated_ids = []
    error_ids = []
    items_copied = 0
    num_items = odoo8.count_records('res.partner')
    try:
        for records in odoo13.search_read_paged('res.country.state', page_size=100):
            records.sort(key=lambda record: record['id'])
            for record in records:
                count += 1
                name = unidecode.unidecode(record['name'])
                odoo13_states[name] = record['id']
    except StopIteration: # Probably succeeded if we get through all the records
        print('Finished.')
    except Exception as e: # Fail on any other exception
        print('problem')
        pass

    try:
        for records in odoo8.search_read_paged('res.country.state', page_size=100):
            records.sort(key=lambda record: record['id'])
            for record in records:
                name = unidecode.unidecode(record['name'])
                odoo8_states[record['id']] = name
    except StopIteration: # Probably succeeded if we get through all the records
        print('Finished.')
    except Exception as e: # Fail on any other exception
        pass

    # ----- Countries -------
    try:
        for records in odoo13.search_read_paged('res.country', page_size=100):
            records.sort(key=lambda record: record['id'])
            for record in records:
                count += 1
                name = unidecode.unidecode(record['name'])
                if name not in odoo13_countries:
                    odoo13_countries[name] = record['id']
    except StopIteration: # Probably succeeded if we get through all the records
        print('Finished.')
    except Exception as e: # Fail on any other exception
        print('problem')
        pass

    try:
        for records in odoo8.search_read_paged('res.country', page_size=100):
            records.sort(key=lambda record: record['id'])
            for record in records:
                name = unidecode.unidecode(record['name'])
                odoo8_countries[record['id']] = name
    except StopIteration: # Probably succeeded if we get through all the records
        print('Finished.')
    except Exception as e: # Fail on any other exception
        pass

    not_found_count = 0
    try:
        for records in odoo13.search_read_paged('res.partner', page_size=100):
            for record in records:
                payload = {}
                if isinstance(record['state_id'], list):
                    state_id = record['state_id'][0]
                    if state_id not in odoo8_states:
                        error_ids.append(record['id'])
                    elif odoo8_states[state_id] not in odoo13_states:
                        error_ids.append(record['id'])
                    else:
                        payload['state_id'] = odoo13_states[odoo8_states[state_id]]

                if isinstance(record['country_id'], list):
                    country_id = record['country_id'][0]
                    if country_id not in odoo8_countries:
                        error_ids.append(record['id'])
                    elif odoo8_countries[country_id] not in odoo13_countries:
                        error_ids.append(record['id'])
                    else:
                        payload['country_id'] = odoo13_countries[odoo8_countries[country_id]]

                if payload:
                    try:
                        orm.write('res.partner', record['id'], payload)
                        migrated_ids.append(record['id'])
                        if STOP_ON_ERROR:
                            input('Success.')
                        orm.cr.commit()
                    except IntegrityError as e:
                        pass
                    except Exception as e:
                        error_ids.append(record['id'])
                        orm.cr.rollback()
                        if STOP_ON_ERROR:
                            print("Migrating record {} failed; Reason: {}".format(record['name'], e))
                            traceback.print_exc()
                            input("Press any key to continue...")
                else:
                    error_ids.append(record['id'])

                items_copied += 1
                printProgressBar(items_copied, num_items, prefix = 'Progress:', length = 50, success=len(migrated_ids), failure=len(error_ids))
    except StopIteration: # Probably succeeded if we get through all the records
        print('Finished.')
    except Exception as e: # Fail on any other exception
        traceback.print_exc()
        pass

