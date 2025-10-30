jQuery('ready', () => {
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
        const fieldName = elem.id.slice("fillbutton_".length);
        const fillFieldName = elem.getAttribute('data-fill-field-name');
        const languages = elem.getAttribute('data-languages');
        const id =  django.jQuery('#id_'+fieldName).find(':selected')[0].value;
    
        django.jQuery.ajax({
            url: "/fill_fields/?api_id="+id+"&field_name="+fillFieldName+"&languages="+languages,
            success: function(result) {
                django.jQuery.each(result, (fieldName, value) => {
                    django.jQuery('#id_'+fieldName).val(value);
                });
            }
        });
    });
});