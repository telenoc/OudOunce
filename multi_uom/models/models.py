# -*- coding: utf-8 -*-
from itertools import chain

from odoo import models, fields, api ,_
from datetime import datetime

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    is_multi_units = fields.Boolean('Is Multi Units?')
    uom_cat_id=fields.Many2one(related='uom_id.category_id')
    units_ids = fields.One2many('multi.units', 'product_id', string='Units IDs')

    def _get_combination_info(self, combination=False, product_id=False, add_qty=1, pricelist=False, parent_combination=False, only_template=False):
        """Override for website, where we want to:
            - take the website pricelist if no pricelist is set
            - apply the b2b/b2c setting to the result

        This will work when adding website_id to the context, which is done
        automatically when called from routes with website=True.
        """
        self.ensure_one()

        current_website = False

        if self.env.context.get('website_id'):
            current_website = self.env['website'].get_current_website()
            if not pricelist:
                pricelist = current_website.get_current_pricelist()
    
        combination_info = super(ProductTemplate, self)._get_combination_info(
            combination=combination, product_id=product_id, add_qty=add_qty, pricelist=pricelist,
            parent_combination=parent_combination, only_template=only_template)
        if self.env.context.get('website_id'):
            partner = self.env.user.partner_id
            company_id = current_website.company_id
            product = self.env['product.product'].browse(combination_info['product_id']) or self

            tax_display = self.env.user.has_group('account.group_show_line_subtotals_tax_excluded') and 'total_excluded' or 'total_included'
            taxes = partner.property_account_position_id.map_tax(product.sudo().taxes_id.filtered(lambda x: x.company_id == company_id), product, partner)

            # The list_price is always the price of one.
            quantity_1 = 1

            pro = [(product, quantity_1 or 1.0, partner)]
            if product.units_ids:
                price, rul_id= pricelist._compute_price_rule(pro, muom=product.units_ids[0] or False)[product.id]
                price = taxes.compute_all(price, pricelist.currency_id, quantity_1, product, partner)[tax_display]
                unit = product.units_ids[0].unit_id
            else:
                price, rul_id= pricelist._compute_price_rule(pro, muom=False)[product.id]
                price = taxes.compute_all(price, pricelist.currency_id, quantity_1, product, partner)[tax_display]
                unit = product.uom_id

            if pricelist.discount_policy == 'without_discount':
                list_price = taxes.compute_all(combination_info['list_price'], pricelist.currency_id, quantity_1, product, partner)[tax_display]
            else:
                list_price = price
            has_discounted_price = pricelist.currency_id.compare_amounts(list_price, price) == 1

            combination_info.update(
                price=price,
                list_price=list_price,
                unit=unit,
                has_discounted_price=has_discounted_price,
            )
        
        return combination_info

class Pricelist(models.Model):
    _inherit = "product.pricelist"

    def _compute_price_rule(self, products_qty_partner, date=False, uom_id=False, muom=None):
        """ Low-level method - Mono pricelist, multi products
        Returns: dict{product_id: (price, suitable_rule) for the given pricelist}

        Date in context can be a date, datetime, ...

            :param products_qty_partner: list of typles products, quantity, partner
            :param datetime date: validity date
            :param ID uom_id: intermediate unit of measure
        """
        if not muom:
            return super(Pricelist, self)._compute_price_rule(products_qty_partner)
        else:
            self.ensure_one()
            if not date:
                date = self._context.get('date') or fields.Date.today()
            date = fields.Date.to_date(date)  # boundary conditions differ if we have a datetime
            if not uom_id and self._context.get('uom'):
                uom_id = self._context['uom']
            if uom_id:
                # rebrowse with uom if given
                products = [item[0].with_context(uom=uom_id) for item in products_qty_partner]
                products_qty_partner = [(products[index], data_struct[1], data_struct[2]) for index, data_struct in enumerate(products_qty_partner)]
            else:
                products = [item[0] for item in products_qty_partner]

            if not products:
                return {}

            categ_ids = {}
            for p in products:
                categ = p.categ_id
                while categ:
                    categ_ids[categ.id] = True
                    categ = categ.parent_id
            categ_ids = list(categ_ids)

            is_product_template = products[0]._name == "product.template"
            if is_product_template:
                prod_tmpl_ids = [tmpl.id for tmpl in products]
                # all variants of all products
                prod_ids = [p.id for p in
                            list(chain.from_iterable([t.product_variant_ids for t in products]))]
            else:
                prod_ids = [product.id for product in products]
                prod_tmpl_ids = [product.product_tmpl_id.id for product in products]

            items = self._compute_price_rule_get_items(products_qty_partner, date, uom_id, prod_tmpl_ids, prod_ids, categ_ids)

            results = {}
            for product, qty, partner in products_qty_partner:
                results[product.id] = 0.0
                suitable_rule = False

                # Final unit price is computed according to `qty` in the `qty_uom_id` UoM.
                # An intermediary unit price may be computed according to a different UoM, in
                # which case the price_uom_id contains that UoM.
                # The final price will be converted to match `qty_uom_id`.
                qty_uom_id = self._context.get('uom') or product.uom_id.id
                price_uom_id = product.uom_id.id
                qty_in_product_uom = qty
                if qty_uom_id != product.uom_id.id:
                    try:
                        qty_in_product_uom = self.env['uom.uom'].browse([self._context['uom']])._compute_quantity(qty, product.uom_id)
                    except UserError:
                        # Ignored - incompatible UoM in context, use default product UoM
                        pass

                # if Public user try to access standard price from website sale, need to call price_compute.
                # TDE SURPRISE: product can actually be a template
                price = product.price_compute('list_price')[product.id]

                price_uom = self.env['uom.uom'].browse([qty_uom_id])
                for rule in items:
                    if rule.min_quantity and qty_in_product_uom < rule.min_quantity:
                        continue
                    if is_product_template:
                        if rule.product_tmpl_id and product.id != rule.product_tmpl_id.id:
                            continue
                        if rule.product_id and not (product.product_variant_count == 1 and product.product_variant_id.id == rule.product_id.id):
                            # product rule acceptable on template if has only one variant
                            continue
                    else:
                        if rule.product_tmpl_id and product.product_tmpl_id.id != rule.product_tmpl_id.id:
                            continue
                        if rule.product_id and product.id != rule.product_id.id:
                            continue

                    if rule.categ_id:
                        cat = product.categ_id
                        while cat:
                            if cat.id == rule.categ_id.id:
                                break
                            cat = cat.parent_id
                        if not cat:
                            continue

                    if rule.base == 'pricelist' and rule.base_pricelist_id:
                        #price_tmp = rule.base_pricelist_id._compute_price_rule([(product, qty, partner)], date, uom_id)[product.id][0]  # TDE: 0 = price, 1 = rule
                        price = muom[0].price #rule.base_pricelist_id.currency_id._convert(price_tmp, self.currency_id, self.env.company, date, round=False)
                    else:
                        # if base option is public price take sale price else cost price of product
                        # price_compute returns the price in the context UoM, i.e. qty_uom_id
                        price = muom[0].price #product.price_compute(rule.base)[product.id]

                    convert_to_price_uom = (lambda price: product.uom_id._compute_price(price, price_uom))

                    if price is not False:
                        if rule.compute_price == 'fixed':
                            price = convert_to_price_uom(rule.fixed_price)
                        elif rule.compute_price == 'percentage':
                            price = (price - (price * (rule.percent_price / 100))) or 0.0
                        else:
                            # complete formula
                            price_limit = price
                            price = (price - (price * (rule.price_discount / 100))) or 0.0
                            if rule.price_round:
                                price = tools.float_round(price, precision_rounding=rule.price_round)

                            if rule.price_surcharge:
                                price_surcharge = convert_to_price_uom(rule.price_surcharge)
                                price += price_surcharge

                            if rule.price_min_margin:
                                price_min_margin = convert_to_price_uom(rule.price_min_margin)
                                price = max(price, price_limit + price_min_margin)

                            if rule.price_max_margin:
                                price_max_margin = convert_to_price_uom(rule.price_max_margin)
                                price = min(price, price_limit + price_max_margin)
                        suitable_rule = rule
                    break
                # Final price conversion into pricelist currency
                if suitable_rule and suitable_rule.compute_price != 'fixed' and suitable_rule.base != 'pricelist':
                    if suitable_rule.base == 'standard_price':
                        cur = product.cost_currency_id
                    else:
                        cur = product.currency_id
                    price = cur._convert(price, self.currency_id, self.env.company, date, round=False)

                if not suitable_rule:
                    cur = product.currency_id
                    price = cur._convert(price, self.currency_id, self.env.company, date, round=False)

                results[product.id] = (price, suitable_rule and suitable_rule.id or False)

            return results

    @api.model
    def get_prices(self, args):

        partner = self.env.user.partner_id
        product = self.env['product.product'].browse(int(args['product_id']))
        pro = [(product, 1.0, partner)]
        
        muom = self.env['multi.units'].browse(int(args['uom']))
        pricelist = self.env['product.pricelist'].browse(int(args['pricelist_ids']))
        price, rul_id = pricelist._compute_price_rule(pro, muom=muom)[product.id]

        # print("<<<  ", float_round(price, precision_digits=2))
        return price


class OrderLineUnits(models.Model):
    _name = 'multi.units'

    def get_category(self):
        return self.env.context.get('uom_cat_id')


    price = fields.Float(required=True)
    uom_cat_id=fields.Many2one('uom.category', default=get_category)
    product_id = fields.Many2one('product.template',  ondelete='cascade')
    unit_id = fields.Many2one('uom.uom', string="Unit", required=True)


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    units_ids = fields.Many2one('multi.units')
