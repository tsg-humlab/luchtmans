(function() {
    jQuery(document).ready(() => {
        django.jQuery('#id_title').on('keyup', (e) => {
            updateUrlParameters('add_id_work', 'title', e.currentTarget.value)
        });

        django.jQuery('#id_languages').on('change', (e) => {
            const language_ids = django.jQuery(e.currentTarget).val().join(",");
            updateUrlParameters('add_id_work', 'languages', language_ids);
        });
    });
})();