$(function () {
    var TEMPLATE = {};
    $("script[type=text/x-mustache-template]").each(function (idx, o) {
        var $o = $(o);
        TEMPLATE[$o.attr("name")] = $o.html();
    });
    function loaded(doc) {
        var res = doc.results;
        doc.match_count = res.length;
        doc.groups = [];
        doc.visible_columns = $.grep(
            doc.columns,
            function (s, i) { return s.charAt(0) != '_'; });
        var group = null;
        for (var i=0; i < res.length; i++) {
            var r = res[i];
            if (!group || group.name !== r.__group__) {
                group = {name: r.__group__, rows: [], match_count: 0};
                doc.groups.push(group);
            }
            group.rows.push({
                'class': 'color' + (r.__color__ || '3') + '-' + ((group.match_count % 2) ? 'odd' : 'even'),
                'cells': $.map(doc.visible_columns, function (k, i) {
                    return {'class': k.toLowerCase(), 'value': r[k]};
                })
            });
            group.match_count++;
        }
        document.title = '{' + doc.report_id + '} ' + doc.title;
        $("#altlinks").html(Mustache.to_html(TEMPLATE.altlinks, doc));
        $("#content").html(Mustache.to_html(TEMPLATE.report, doc));

        console.log(doc);
    }
    $.getJSON(window.location.href, loaded);
})