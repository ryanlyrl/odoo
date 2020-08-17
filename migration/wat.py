

def somefunc(odoo):
    reg = odoo.registry("13_test")
    cr = reg.cursor()
    uid = odoo.SUPERUSER_ID
    env = odoo.api.Environment(cr, uid, context={})

    print(env['res.users'].search([]))


    cr.close()
