# -*- coding: utf-8 -*-
import logging
import werkzeug.utils

from odoo import http
from odoo.http import content_disposition, Controller, request, route
import json
from odoo.tools import float_round


class WebsiteUOM(http.Controller):
    
    @http.route(['/shop/cart/update'], type='http', auth="public", methods=['GET', 'POST'], website=True, csrf=False)
    def cart_update(self, product_id, add_qty=1, set_qty=0, **kw):
        """This route is called when adding a product to cart (no options)."""
        sale_order = request.website.sale_get_order(force_create=True)
        if sale_order.state != 'draft':
            request.session['sale_order_id'] = None
            sale_order = request.website.sale_get_order(force_create=True)

        product_custom_attribute_values = None
        if kw.get('product_custom_attribute_values'):
            product_custom_attribute_values = json.loads(kw.get('product_custom_attribute_values'))

        no_variant_attribute_values = None
        if kw.get('no_variant_attribute_values'):
            no_variant_attribute_values = json.loads(kw.get('no_variant_attribute_values'))

        pricelist = None
        if kw.get('pricelist'):
            pricelist = kw.get('pricelist')

        sale_order._cart_update(
            product_id=int(product_id),
            add_qty=add_qty,
            set_qty=set_qty,
            pricelist=pricelist,
            uom=kw['uom'],
            product_custom_attribute_values=product_custom_attribute_values,
            no_variant_attribute_values=no_variant_attribute_values
        )

        if kw.get('express'):
            return request.redirect("/shop/checkout?express=1")

        return request.redirect("/shop/cart")


    @route(['/get/price'], type='json', auth="public", methods=['GET', 'POST'], csrf=False)
    def get_price(self, **args):
        
        partner = request.env.user.partner_id
        product = request.env['product.product'].browse(int(args['product_id']))
        pro = [(product, 1.0, partner)]
        
        muom = request.env['multi.units'].browse(int(args['uom']))
        pricelist = request.env['product.pricelist'].browse(int(args['pricelist_ids']))
        price, rul_id = pricelist._compute_price_rule(pro, muom=muom)[product.id]
        
        values = {}
        values.update({
                 "price":float_round(price, precision_digits=2),
                 "currency":product.currency_id.name,
               })
        return values