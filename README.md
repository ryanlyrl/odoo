# Toys on Fire Odoo 13 Migration
This is a tool written by Ryan Ly for migrating Toys on Fire's Odoo database from Odoo 8 to Odoo 13.

## Migration Tool
Running the tool:
1. From the root of the project: `./odoo-bin shell`
2. `from migration import test`
3. `test.run(odoo, <table_name>)`

The database names and credentials may need to be changed in `test.py`.
 
## Dependency Tool
To generate an image of dependencies, ignoring nullable fields:

`python3 finddeps.py --db <db> --user <username> --password <password> <tables> | dot -Tpng > deps_notnull.png`

To generate an image of dependencies with nullable fields:

`python3 finddeps.py --db <db> --user <username> --password <password> <tables> --null | dot -Tpng > deps_notnull.png`