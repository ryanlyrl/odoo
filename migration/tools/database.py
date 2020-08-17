import psycopg2

DEP_QUERY = '''
SELECT
    tc.constraint_name, tc.table_name, kcu.column_name,
    ccu.table_name AS foreign_table_name,
    ccu.column_name AS foreign_column_name
FROM
    information_schema.table_constraints AS tc
JOIN information_schema.key_column_usage AS kcu ON
    tc.constraint_name = kcu.constraint_name
JOIN information_schema.constraint_column_usage AS ccu ON
    ccu.constraint_name = tc.constraint_name
JOIN information_schema.columns AS col ON
    col.column_name = kcu.column_name AND col.table_name = tc.table_name
WHERE constraint_type = 'FOREIGN KEY' AND tc.table_name = '{}'
'''

class Database:

    def __init__(self, host, db, username, password):
        try:
            self.connection = psycopg2.connect("host='{}' dbname='{}' user='{}' password='{}'".format(host, db, username, password))
        except psycopg2.OperationalError:
            print('Error connecting to Postgres database')
            self.connection = None

        self.cursor = self.connection.cursor()

    def get_all_tables(self):
        self.cursor.execute("SELECT tablename FROM pg_tables WHERE schemaname='public'")
        return [row[0] for row in self.cursor.fetchall()]

    def get_dependencies(self, table, get_nullable=False):
        query = DEP_QUERY
        if not get_nullable:
            query += " AND col.is_nullable = 'NO'"
        self.cursor.execute(query.format(table))
        return [[row[1], row[3]] for row in self.cursor.fetchall()]
