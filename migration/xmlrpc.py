import xmlrpc.client

DEFAULT_PAGE_LIMIT = 100

class XmlrpcLib:


    def __init__(self, url, db, username, password):
        self.url = url
        self.db = db
        self.username = username
        self.password = password
        self.common = xmlrpc.client.ServerProxy('{}/xmlrpc/2/common'.format(url))
        self.models = xmlrpc.client.ServerProxy('{}/xmlrpc/2/object'.format(url))
        self.uid = self.common.authenticate(db, username, password, {})


    def search(self, table, domain=[]):
        return self.models.execute_kw(self.db, self.uid, self.password,
            table, 'search', [domain])


    def count_records(self, table, domain=[]):
        return self.models.execute_kw(self.db, self.uid, self.password,
            table, 'search_count', [domain])


    def read(self, table, ids, fields=None):
        assert ids, "IDs must be provided"

        if fields:
            return self.models.execute_kw(self.db, self.uid, self.password,
                table, 'read', [ids], {'fields': fields})
        else:
            return self.models.execute_kw(self.db, self.uid, self.password,
                table, 'read', [ids])


    def search_read(self, table, domain=[], fields=None, limit=0, offset=0):
        options = {}
        if fields:
            options['fields'] = fields
        if limit:
            options['limit'] = limit
        if offset:
            options['offset'] = offset

        if options:
            return self.models.execute_kw(self.db, self.uid, self.password,
                table, 'search_read', [domain], options)
        else:
            return self.models.execute_kw(self.db, self.uid, self.password,
                table, 'search_read', [domain])


    def search_read_paged(self, table, domain=[], fields=None, page_size=DEFAULT_PAGE_LIMIT):
        current_offset = 0
        records = self.search_read(table, domain, fields=fields, limit=page_size, offset=current_offset)
        while True:
            if current_offset != 0 and len(records) < page_size:
                return
            yield records
            current_offset += page_size
            records = self.search_read(table, domain, fields=fields, limit=page_size, offset=current_offset)


    def create_record(self, table, values):
        return self.models.execute_kw(self.db, self.uid, self.password,
            table, 'create', [values])


    def update_record(self, table, id, values):
        return self.models.execute_kw(self.db, self.uid, self.password,
            table, 'write', [[id], values])

    
    def delete_record(self, table, id):
        self.models.execute_kw(self.db, self.uid, self.password,
            table, 'unlink', [[id]])


    def get_fields(self, table):
        return [field for field in self.models.execute_kw(self.db, self.uid, self.password,
        table, 'fields_get', [])]


    def get_version(self):
        return self.common.version()