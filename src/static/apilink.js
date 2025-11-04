function defaultTemplateResult(option) {
    const text = option.text.trim();
    if(text.startsWith('<div>')) {
        return django.jQuery(option.text);
    }
    return option.text;
}

jQuery('ready', () => {
    // Allow HTML in options
    django.jQuery('.django-select2').select2.defaults.defaults.templateResult = defaultTemplateResult;
    django.jQuery('.django-select2').select2.defaults.defaults.templateSelection = defaultTemplateResult;

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