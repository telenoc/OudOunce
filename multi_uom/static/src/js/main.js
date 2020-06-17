odoo.define('multi_uom.uom_portal', function (require) {
    'use strict';
    
    var publicWidget = require('web.public.widget');
    var rpc = require('web.rpc')
    var core = require('web.core');
    var _t = core._t;

    publicWidget.registry.portalUOM = publicWidget.Widget.extend({
        selector: '.o_portal_uom',
        events: {
            'change select[name="uom"]': '_onProductChange',
        },
    
        /**
         * @override
         */
        start: function () {
            var def = this._super.apply(this, arguments);
            return def;
        },
        //--------------------------------------------------------------------------
        // Handlers
        //--------------------------------------------------------------------------
    
        /**
         * @private
         */
        _adaptAddressForm: function () {
            
            rpc.query({
                model: 'product.pricelist',
                method: 'get_prices',
                args: [{
                    'product_id': $('.product_id').val(),
                    'pricelist_ids': $('.pricelist_ids').val(),
                    'uom': $('.uom').val(),
                }]
            }).then(function (result) {
                $(".oe_price").html(result)
            }); 
        },

        /**
         * @private
         */
        _onProductChange: function (ev) {

            this._adaptAddressForm();
            
        },
    });
    

    
    });
    