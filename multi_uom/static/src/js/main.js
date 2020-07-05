odoo.define('multi_uom.uom_portal', function (require) {
    'use strict';
    
    
    var publicWidget = require('web.public.widget');
    var rpc = require('web.rpc')


    publicWidget.registry.portalUOM = publicWidget.Widget.extend({
        selector: '.o_portal_uom',
        events: {
            'change select[name="uom"]': '_adaptAddressForm',
        },
        /**
         * @override
         */
        start: function () {
            var def = this._super.apply(this, arguments);
            var self = this;

            self._rpc({
                route: '/get/price',
                            params: { 
                                product_id: $('.product_id').val(),
                                pricelist_ids: $('.pricelist_ids').val(),
                                uom: $('.uom').val(),
                            },
            }).then(function (result) {
                    $(".oe_price").html(result.price + " " + result.currency)
                }); 

            // $.get("/get/price", {
            //                 product_id: $('.product_id').val(),
            //                 pricelist_ids: $('.pricelist_ids').val(),
            //                 uom: $('.uom').val(),
            // }).then(function (data) {
            //     console.log("ddddddddddddddddddd    ", data)
            // });
            // rpc.query({
            //     model: 'product.pricelist',
            //     method: 'get_prices',
            //     args: [{
            //         'product_id': $('.product_id').val(),
            //         'pricelist_ids': $('.pricelist_ids').val(),
            //         'uom': $('.uom').val(),
            //     }]
            // }).then(function (result) {
            //     $(".oe_price").html(result.price + " " + result.currency)
            // }); 
            return def;
        },
        //--------------------------------------------------------------------------
        // Handlers
        //--------------------------------------------------------------------------
    
        /**
         * @private
         */
        _adaptAddressForm: function () {
            var self = this;
            self._rpc({
                route: '/get/price',
                            params: { 
                                product_id: $('.product_id').val(),
                                pricelist_ids: $('.pricelist_ids').val(),
                                uom: $('.uom').val(),
                            },
            }).then(function (result) {
                    $(".oe_price").html(result.price + " " + result.currency)
                });
            // rpc.query({
            //     model: 'product.pricelist',
            //     method: 'get_prices',
            //     args: [{
            //         'product_id': $('.product_id').val(),
            //         'pricelist_ids': $('.pricelist_ids').val(),
            //         'uom': $('.uom').val(),
            //     }]
            // }).then(function (result) {
            //     $(".oe_price").html(result.price + " " + result.currency)
            // }); 
        },

        /**
         * @private
         */
        _onProductChange: function (ev) {

            this._adaptAddressForm();
            
        },
    });
    

    
    });
    