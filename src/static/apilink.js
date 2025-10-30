jQuery('ready', () => {
    django.jQuery('.django-select2-apilink').on('change', (e) => {
        const fieldName = e.currentTarget.id.slice("id_".length);
        const id =  django.jQuery('#id_'+fieldName).find(':selected')[0].value
        const link = django.jQuery('#apilink_'+fieldName);
        link.attr("href", link.attr("href_base")+id);
        if(id) {
            link[0].style.display = 'inline';
        } else {
            link[0].style.display = 'none';
        }
    });
});