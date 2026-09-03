/**
 * Add/update the url query parameters
 * @param id ID of the element that has it's url (href) changed
 * @param name Name of the query parameter
 * @param value Value of the query parameter
 */
function updateUrlParameters(id, name, value) {
    const url_elem = django.jQuery('#'+id)[0];
    const url = new URL(url_elem.href, window.location.origin);
    url.searchParams.set(name, value);
    url_elem.href = url;
}