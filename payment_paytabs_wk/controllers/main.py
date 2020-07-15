import logging
_logger = logging.getLogger(__name__)
from odoo import http
from odoo.tools.translate import _
from odoo.http import request
from odoo.addons.website_sale.controllers.main import WebsiteSale
import requests
from ast import literal_eval
import json
import werkzeug.utils
from werkzeug.exceptions import BadRequest
from odoo.service import common



class WebsiteSale(WebsiteSale):
	_paytabs_feedbackUrl='/payment/paytabs/feedback'

	@http.route([_paytabs_feedbackUrl], type='json', auth='public', website=True)
	def paytabs_payment(self, **post):
		merchant_detail = request.env["payment.acquirer"].sudo().browse(int(post.get('acquirer',0)))
		partner = request.env.user.partner_id
		products,qty,price_unit,sale_order_detail,billing_address,address_shipping = merchant_detail.create_paytabs_params(partner,post)
		request.session['so_id']= post.get("reference")

		version_info = common.exp_version()
		server_serie =version_info.get('server_serie')
		total_amount = literal_eval(post.get('amount'))
		# + sale_order_detail.amount_tax
		paytabs_tx_values = {
					 'merchant_email': merchant_detail.detail_payment_acquire().get('paytabs_merchant_email'),
					 'secret_key': merchant_detail.detail_payment_acquire().get('paytabs_client_secret'),
					 'site_url': merchant_detail.detail_payment_acquire().get('paytabs_site_url'),
					 'pay_page_url': merchant_detail.paytabs_url().get('pay_page_url'),
					 'return_url': merchant_detail.paytabs_url().get('return_url'),
					 'title': request.env['website'].search([])[0].name,
					 'currency': post.get('currency'),
					 'amount': total_amount,
					 'quantity': qty,
					 'unit_price': price_unit,
					 'discount': "0",
					 'other_charges': str(sale_order_detail.amount_tax) or 0 ,
					#  'other_charges': "0" ,
					 'cc_first_name': partner.name,
					 'cc_last_name': partner.name,
					 'cc_phone_number': partner.phone,
					 'phone_number': partner.phone or sale_order_detail.partner_id.phone,
					 'email': partner.email or sale_order_detail.partner_id.email,
					 'products_per_title': products,
					 'msg_lang': partner.lang,
					 'country_shipping': address_shipping.country_id.code2 or partner.country_id.code2 ,
					 'postal_code_shipping': address_shipping.zip or partner.zip ,
					 'state_shipping':  address_shipping.state_id.name or partner.state_id.name ,
					 'city_shipping':  address_shipping.city or partner.city ,
					 'address_shipping': address_shipping.street or partner.street ,
					 'billing_address': billing_address and billing_address.street or partner.street,
					 'shipping_last_name': partner.name,
					 'shipping_first_name': partner.name,
					 'country': partner.country_id.code2  or  sale_order_detail.partner_id.country_id.code2,
					 'postal_code': partner.zip or sale_order_detail.partner_id.zip,
					 'reference_no': post.get("reference"),
					 'state': partner.state_id.name or sale_order_detail.partner_shipping_id.name,
					 'city': partner.city or sale_order_detail.partner_shipping_id.name,
					 'ip_merchant': request.env['ir.config_parameter'].sudo().get_param('web.base.url'),
					 'ip_customer': request.httprequest.environ['REMOTE_ADDR'],
					 'cms_with_version': "ODOO "+ server_serie
					 }
		result = requests.post(url= merchant_detail.paytabs_url().get('pay_page_url'), data=paytabs_tx_values)
		request_params = literal_eval(result.text)
		_logger.info("-----request_params-%r-",request_params)
		return request_params
		# if request_params.get("p_id") and request_params.get("result") == "The Pay Page is created." and request_params.get("response_code") == "4012" and request_params.get("payment_url"):
		# 	return werkzeug.utils.redirect(request_params.get("payment_url"))
		# elif request_params.get("result") == "The Pay Page is created." and request_params.get("response_code") == "4012" and request_params.get("payment_url"):
		# 	_logger.info("--p_id is zero--request_params.get('p_id')---%r-",request_params.get("p_id"))
		# 	return werkzeug.utils.redirect(request_params.get("payment_url"))






	@http.route(['/paytabs/feedback'], type='http', auth='public', website=True ,csrf=False)
	def paytabs_feedback(self, **post):
		merchant_detail = request.env["payment.acquirer"].sudo().search([("provider","=","paytabs"),("state","!=","disabled")], limit=1)
		try:
			params = {
				'merchant_email': merchant_detail.detail_payment_acquire().get('paytabs_merchant_email'),
				'secret_key': merchant_detail.detail_payment_acquire().get('paytabs_client_secret'),
		  		'payment_reference': post.get('payment_reference')
		 	 }
			result = requests.post(url= merchant_detail.paytabs_url().get('verify_payment'), data=params)
			request_params = json.loads(result.text)
		except Exception as e:
			request_params = {
					'status':'cancel',
					"reference_no": request.session.get('so_id'),
					'result': 'The payment is cancelled successfully!',
					'response_code': '403'
			}
			request.session.pop('so_id', None)
		request.env['payment.transaction'].form_feedback(request_params, 'paytabs')
		return werkzeug.utils.redirect('/payment/process')
