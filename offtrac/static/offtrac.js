$(function () {
    function loaded(doc) {
        console.log(doc);
    }
    $.getJSON(window.location.href, loaded);
})