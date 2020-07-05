odoo.define('terms_conditionadd_medicines.terms_conditionadd_medicines', function (require) {
"use strict";
    var ajax = require('web.ajax');

    $(document).ready(function () {

        $('.checkbox_cgv').change(function() {

            ajax.jsonRpc('/check/terms-and-condition', 'call', {
                'aggrement': $('.checkbox_cgv').prop('checked')
            });
        });
    });
});
