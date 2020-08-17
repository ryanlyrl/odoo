'''
A tool for generating all the dependencies of a Postgres database
Based on https://sigterm.sh/2010/07/09/generating-a-dependency-graph-for-a-postgresql-database/
'''
import argparse
from database import Database
from graph import Graph

def main():
    parser = argparse.ArgumentParser(description='Generates the dependencies of select tables of a Postgres database')
    parser.add_argument('tables', nargs='+',
                        help='The tables to analyse (as individual arguments)')
    parser.add_argument('--host', default='localhost', help='The host of the database (default: localhost)')
    parser.add_argument('--db', help='The name of the database')
    parser.add_argument('--user', help='The user to access the database as')
    parser.add_argument('--password', help='The user\'s password')
    parser.add_argument('--null', action='store_true', help='Whether to include nullable foreign keys')

    args = parser.parse_args()
    db = Database(args.host, args.db, args.user, args.password)

    if not validate_tables(db, args.tables):
        print('One of the tables provided was invalid. Please make sure the tables exist.')
        return

    deps = find_dependencies(db, args.tables, args.null)

    print('''
    digraph Dependencies {{
        {}
    }}
    '''.format(deps.stringify()))

def validate_tables(db, tables):
    all_tables = db.get_all_tables()
    for table in tables:
        if table not in all_tables:
            return False
    return True

def find_dependencies(db, tables, get_nullable=False):
    graph = Graph()
    tables_to_check = list(tables)
    checked_tables = list(tables)
    while(len(tables_to_check) != 0):
        table = tables_to_check.pop()
        deps = db.get_dependencies(table, get_nullable)
        for table, foreign_table in deps:
            if foreign_table not in checked_tables:
                checked_tables.append(foreign_table)
                tables_to_check.append(foreign_table)
            graph.add_edge(table, foreign_table)

    return graph

if __name__ == "__main__":
    main()