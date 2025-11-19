(function() {
    var map;
    django.jQuery(window).on('map:init', function(e) {
        var detail = e.originalEvent ? e.originalEvent.detail : e.detail;
        map = detail.map;
    });

    django.jQuery(document).ready(() => {
        map.setZoom(6);

        // Allow HTML in options
        django.jQuery('.django-select2-apilink').djangoSelect2({
            templateResult: (option) => { return django.jQuery(option.text) },
            templateSelection: (option) => { return django.jQuery(option.text) }
        });

        // Change API link
        django.jQuery('.django-select2-apilink').on('change', (e) => {
            const fieldName = e.currentTarget.id.slice("id_".length);
            const id =  django.jQuery('#id_'+fieldName).find(':selected')[0].value;
            const link = django.jQuery('#apilink_'+fieldName);
            link.attr("href", link.attr("href_base")+id);
            django.jQuery('#api_block_'+fieldName)[0].style.display = id ? 'inline' : 'none';
        });

        // Fill in button
        django.jQuery('.fill-button').on('click', (e) => {
            const elem = e.currentTarget;
            const original_elem_text = elem.text;
            const fieldName = elem.id.slice("fillbutton_".length);
            const fillFieldName = elem.getAttribute('data-fill-field-name');
            const id =  django.jQuery('#id_'+fieldName).find(':selected')[0].value;

            django.jQuery.ajax({
                url: "/fill_fields/"+fillFieldName+"/?api_id="+id,
                beforeSend: function() {
                    elem.text = 'Fetching data...';
                },
                success: function(result) {
                    django.jQuery.each(result, (fieldName, data) => {
                        const field = django.jQuery('#id_'+fieldName);
                        if (field.hasClass("select2-hidden-accessible")) {
                            if (field.find("option[value='" + data.id + "']").length) {
                                field.val(data.id).trigger('change');
                            } else {
                                // Create a DOM Option and pre-select by default
                                var newOption = new Option(data.text, data.id, true, true);
                                // Append it to the select
                                field.append(newOption).trigger('change');
                            }
                        } else if(field.hasClass('django-leaflet-raw-textarea')) {
                            map.eachLayer((layer) => {
                                if(layer['_latlng']!=undefined)
                                    layer.remove();
                            });
                            const coordinates = JSON.parse(data)['coordinates'];
                            L.marker([coordinates[1],coordinates[0]]).addTo(map);
                            field.val(data);
                        } else {
                            field.val(data);
                        }
                    });
                },
                complete: function() {
                    elem.text = original_elem_text;
                }
            });
        });
    });
})();