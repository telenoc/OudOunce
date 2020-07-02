# -*- coding: utf-8 -*-
from odoo.addons.website_sale.controllers.main import WebsiteSale
import odoo.http as http
from odoo.http import request


class WebsiteSaleOptions(WebsiteSale):
    
    @http.route(['/check/terms-and-condition'], type='json', auth="public", website=True)
    def check_terms_and_condition(self, **kwargs):
        sale_order = request.website.sale_get_order()
        if kwargs.get('aggrement')==True:
            sale_order.agreement = kwargs.get('aggrement')
        if kwargs.get('aggrement')==False:
            sale_order.agreement = kwargs.get('aggrement')
