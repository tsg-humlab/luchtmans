(function() {
    // Gather maps using the field name taken from the container ID
    window.maps = {};
    L.Map.addInitHook(function () {
        window.maps[this._container.id.slice(3,-4)] = this;
    });

    django.jQuery(document).ready(() => {
        // Set zoom for all maps
        for(const [fieldName, map] of Object.entries(window.maps)) {
            const map_textarea = django.jQuery('#id_'+fieldName);
            const form_id = map_textarea.parents('form')[0].id
            if(map_textarea.text() == '') {
                // Creating
                if(form_id.startsWith('country')) {
                    map.setZoom(4);
                } else if(form_id.startsWith('place')) {
                    map.setZoom(6);
                } else {
                    map.setZoom(7);
                }
            } else {
                // Editing
                if(form_id.startsWith('country')) {
                    map.setZoom(5);
                } else if(form_id.startsWith('place')) {
                    map.setZoom(9);
                } else {
                    map.setZoom(13);
                }
            }
        }

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
                            const map = window.maps[fieldName];
                            map.eachLayer((layer) => {
                                if(layer['_latlng']!=undefined)
                                    layer.remove();
                            });
                            const coordinates = JSON.parse(data)['coordinates'];
                            const latlng = [coordinates[1],coordinates[0]];
                            L.marker(latlng).addTo(map);
                            if(fillFieldName.startsWith('country')) {
                                map.setView(latlng, 5);
                            } else if(fillFieldName.startsWith('place')) {
                                map.setView(latlng, 9);
                            } else {
                                map.setView(latlng, 13);
                            }
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