$(function () {
    var TEMPLATE = {};
    $("script[type=text/x-mustache-template]").each(function (idx, o) {
        var $o = $(o);
        TEMPLATE[$o.attr("name")] = $o.html();
    });
    function iso_date(d) {
        function pad(n) {
            return ((n < 10) ? '0' + n : n);
        }
        return (d.getUTCFullYear() + '-'
          + pad(d.getUTCMonth() + 1) + '-'
          + pad(d.getUTCDate()));
    }
    var title_postfix = ' MochiMedia [offtrac]';
    function report(doc) {
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
                    var v = r[k];
                    var fv = null;
                    var cls = k.toLowerCase();
                    if (cls === 'created' || cls === 'reported' || cls === 'due') {
                        v = ((v) ? iso_date(new Date(v)) : '');
                    } else if (cls === 'ticket' || cls === 'summary') {
                        fv = Mustache.to_html(TEMPLATE.ticket_link,
                            {'ticket_id': r.ticket, 'value': ((cls === 'ticket') ? '#' : '') + v });
                    }
                    return {'class': cls, 'value': v, 'html_value': fv};
                })
            });
            group.match_count++;
        }
        document.title = '{' + doc.report_id + '} ' + doc.title + title_postfix;
        $("#altlinks").html(Mustache.to_html(TEMPLATE.altlinks, doc));
        $("#content").html(Mustache.to_html(TEMPLATE.report, doc));
    }
    function report_list(doc) {
        document.title = doc.title + title_postfix;
        $("#content").html(Mustache.to_html(TEMPLATE.report_list, doc));
    }
    function ticket(doc) {
        console.log(doc);
        var t = doc.ticket;
        document.title = '#' + t.id + ' ' + t.summary + title_postfix;
        $("#content").html(Mustache.to_html(TEMPLATE.ticket, doc));
    }
    function loaded(doc) {
        if (doc.template === 'report') {
            report(doc);
        } else if (doc.template === 'report_list') {
            report_list(doc);
        } else if (doc.template === 'ticket') {
            ticket(doc);
        }
    }
    function json_url(url) {
        return url + (url.indexOf('?') === -1 ? '?' : '&') + 'format=json';
    }
    $.getJSON(json_url(window.location.href), loaded);
})