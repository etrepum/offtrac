$(function () {
    var TEMPLATE = {};
    var NOW = new Date();
    var CREOLE = new Parse.Simple.Creole({});
    $("script[type=text/x-mustache-template]").each(function (idx, o) {
        var $o = $(o);
        TEMPLATE[$o.attr("name")] = $o.html();
    });

    var HTML_ENTITIES = {
      '&': '&amp;',
      '>': '&gt;',
      '<': '&lt;',
      '"': '&quot;',
      "'": '&#32;'
    };
    function html_escape(text) {
        return text && text.replace(/[&"'><]/g, function (character) {
            return HTML_ENTITIES[character];
        });
    }
    function trunc_day(dt) {
        return new Date(dt.getFullYear(), dt.getMonth(), dt.getDate());
    }
    function day_before(dt) {
        return trunc_day(
            new Date(trunc_day(dt).getTime() - (3 * 3600 * 1000)));
    }
    function date_diff(d1, d0) {
        return d1.getTime() - d0.getTime();
    }
    function elapsed_time(elapsed) {
        elapsed = Math.abs(elapsed);
        var TIMEFRAMES = [
            [(86400 * 365 * 1000), 'years'],
            [(86400 * 30 * 1000), 'months'],
            [(86400 * 7 * 1000), 'weeks'],
            [(86400 * 1000), 'days'],
            [(3600 * 1000), 'hours'],
            [(60 * 1000), 'minutes'],
            [(1 * 1000), 'seconds'],
        ];
        var i;
        for (i = 0; (i < TIMEFRAMES.length - 1) &&
                (elapsed < (2 * TIMEFRAMES[i][0])); i++) {
            /* find appropriate unit */
        }
        var unit = TIMEFRAMES[i];
        return Math.floor(elapsed / unit[0]) + ' ' + unit[1];
    }
    function iso_date(d) {
        function pad(n) {
            return ((n < 10) ? '0' + n : n);
        }
        return (d.getUTCFullYear() + '-'
          + pad(d.getUTCMonth() + 1) + '-'
          + pad(d.getUTCDate()));
    }
    function parse_search_query(s) {
        var terms = [];
        var re = /(?:((?:".*?")|(?:'.*?'))|([^\s]+))(?:\s*)/g;
        var match = null;
        while ((match = re.exec(s)) !== null) {
            var quoted = match[1];
            if (quoted) {
                terms.push(quoted.substring(1, quoted.length - 1))
            } else {
                terms.push(match[2]);
            }
        }
        return terms;
    }
    var title_postfix = ' MochiMedia [offtrac]';
    function link_tickets(text) {
        var ticketregex = /(^|[^0-9A-Z&\/\?!]+)(!?#)([0-9]+)/gi;
        return text.replace(ticketregex, function(match, before, hash, text) {
            if (hash.charAt(0) === '!') {
                return before + '#' + hash + text;
            }
            hash = html_escape(hash);
            text = html_escape(text);
            return (before +
                '<a href=\"/ticket/' + text + '\">' + hash + text + '</a>');
        });
    }
    function wiki_format(text, render) {
        var t = twttr.txt;
        var txt = render(text).split("\n").join("<br />\n");
        var d = document.createElement('div');
        CREOLE.parse(d, render(text));
        return link_tickets(d.innerHTML);
    }
    function ago_format(text, render) {
        var et = parseFloat(render(text)) - NOW.getTime();
        return elapsed_time(et) + ' ' + ((et < 0) ? 'ago' : 'from now') + ' ';
    }
    function capitalize(s) {
        return s.charAt(0).toUpperCase() + s.slice(1);
    }
    function report(doc) {
        var res = doc.results;
        doc.match_count = res.length;
        doc.groups = [];
        doc.visible_columns = $.grep(
            doc.columns,
            function (s, i) { return s.charAt(0) != '_'; });
        var group = null;
        var prefix = doc.group ? capitalize(doc.group) + ': ' : '';
        for (var i=0; i < res.length; i++) {
            var r = res[i];
            if (!group || group.id !== r.__group__) {
                group = {name: prefix + r.__group__, id: r.__group__, rows: [], match_count: 0};
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
        document.title = (doc.report_id ? '{' + doc.report_id + '} ' : '') + doc.title + title_postfix;
        $("#altlinks").html(Mustache.to_html(TEMPLATE.altlinks, doc));
        $("#content").html(Mustache.to_html(TEMPLATE.report, doc));
    }
    function report_list(doc) {
        document.title = doc.title + title_postfix;
        $("#content").html(Mustache.to_html(TEMPLATE.report_list, doc));
    }
    function milestone_list(doc) {
        document.title = doc.title + title_postfix;
        $.each(doc.milestones, function (i, o) {
            o.pct_closed = Math.round((100.0 * o.closed) / o.total);
            o.pct_open = 100 - o.pct_closed;
            o.qname = encodeURIComponent(o.name).replace(/%20/g, '+');
            if (o.due) {
                var due = new Date(o.due);
                o.elapsed = date_diff(due, NOW);
                var et = elapsed_time(o.elapsed);
                var dt = '(' + iso_date(due) + ')';
                if (o.elapsed < 0) {
                    o.due_ago = '<strong>' + et + ' late </strong> ' + dt;
                } else {
                    o.due_ago = 'Due in ' + et + ' ' + dt;
                }
            } else {
                o.due_ago = 'No date set';
            }
        });
        $("#content").html(Mustache.to_html(TEMPLATE.milestone_list, doc));
    }
    function group_comments(changes) {
        var comments = [];
        var comment = null;
        function comment_has_changes() {
            return this.changed.length;
        }
        $.each(changes, function (idx, value) {
            var ts = 1000 * Math.floor(value.time * 0.001);
            if (comment === null || ts > comment.time ||
                    comment.author !== value.author ||
                    comment.ticket !== value.ticket) {
                comment = {
                    time: ts,
                    author: value.author,
                    changed: [],
                    ticket: value.ticket,
                    date: iso_date(new Date(ts)),
                    has_changes: comment_has_changes};
                comments.push(comment);
            }
            if (value.field === 'comment') {
                comment.cnum = value.oldvalue;
                comment.comment = value.newvalue;
            } else {
                value.field_title = capitalize(value.field);
                comment.changed.push(value);
            }
        });
        $.each(comments, function (idx, value) {
            value.changed.sort(function (a, b) { return (b < a) - (a < b); });
        });
        return comments;
    }
    function list_of(s) {
        return s.split(/[ \t,]+/);
    }
    function list_to_set(lst) {
        var rval = {};
        $.each(lst, function (idx, v) { rval[v] = idx; });
        return rval;
    }
    function list_diff(oldvalue, newvalue) {
        var added = [];
        var removed = [];
        var oldlst = list_of(oldvalue);
        var newlst = list_of(newvalue);
        var oldset = list_to_set(oldlst);
        var newset = list_to_set(newlst);
        return {
            added: $.grep(newlst, function (elem, idx) {
                return !(elem in oldset); }),
            removed: $.grep(oldlst, function (elem, idx) {
                return !(elem in newset); })};
    }
    function change_format(text, render) {
        if (this.field === 'description') {
            /* TODO: implement diff here */
            return ' modified (TODO: diff)';
        }
        var t;
        this.added = '';
        this.removed = '';
        if (this.field === 'keywords' || this.field == 'cc') {
            var diff = list_diff(this.oldvalue, this.newvalue);
            this.added = diff.added.join(", ");
            this.removed = diff.removed.join(", ");
        }
        if (this.added || this.removed) {
            var lst = [];
            if (this.added) {
                lst.push('<em>{{added}}</em> added');
            }
            if (this.removed) {
                lst.push('<em>{{removed}}</em> removed');
            }
            t = lst.join('; ');
        } else if (this.oldvalue && this.newvalue) {
            t = 'changed from <em>{{oldvalue}}</em> to <em>{{newvalue}}</em>';
        } else if (this.oldvalue) {
            t = '<em>{{oldvalue}}</em> deleted'
        } else {
            t = 'set to <em>{{newvalue}}</em>';
        }
        return (' ' + render(t) + ' ');
    }
    function ticket(doc) {
        var t = doc.ticket;
        t.comments = group_comments(t.changes);
        /*
        TODO:

            Changes should be displayed as trac does it
             * Description diff
        */
        document.title = '#' + t.id + ' ' + t.summary + title_postfix;
        $("#content").html(Mustache.to_html(TEMPLATE.ticket, doc));
    }
    function timeline_day_groups(comments, tickets) {
        var days = [];
        var day = null;
        var today = iso_date(trunc_day(NOW));
        var yesterday = iso_date(day_before(NOW));
        for (var i = comments.length - 1; i >= 0; i--) {
            var o = comments[i];
            o.t = tickets[o.ticket];
            o.status_class = 'newticket';
            o.summary = o.t.summary;
            if (day === null || o.date !== day.date) {
                day = {date: o.date, day_changes: []};
                if (o.date === today) {
                    day.today_or_yesterday = 'Today';
                } else if (o.date === yesterday) {
                    day.today_or_yesterday = 'Yesterday';
                }
                days.push(day);
            }
            day.day_changes.push(o);
        }
        return days;
    }
    function timeline(doc) {
        var tickets = doc.tickets;
        var comments = group_comments(doc.changes);
        doc.days = timeline_day_groups(comments, tickets);
        document.title = doc.title + title_postfix;
        console.log(doc);
        $("#content").html(Mustache.to_html(TEMPLATE.timeline, doc));
    }
    function index(doc) {
        document.title = doc.title + title_postfix;
        $("#content").html(Mustache.to_html(TEMPLATE.index, doc));
    }
    function loaded(doc) {
        doc.wiki_format = function () { return wiki_format };
        doc.change_format = function () { return change_format };
        doc.ago = function () { return ago_format; }
        if (doc.user) {
            $("span.username").html(doc.user);
        }
        if (doc.template === 'report') {
            report(doc);
        } else if (doc.template === 'report_list') {
            report_list(doc);
        } else if (doc.template === 'milestone_list') {
            milestone_list(doc);
        } else if (doc.template === 'ticket') {
            ticket(doc);
        } else if (doc.template === 'index') {
            index(doc);
        } else if (doc.template === 'timeline') {
            timeline(doc);
        }/* else if (doc.template === 'search') {
            trac_search(doc);
        }*/
        if (old_hash) {
            window.location.hash = old_hash;
        }
    }
    function json_url(url) {
        url = url.split('#')[0];
        return url + (url.indexOf('?') === -1 ? '?' : '&') + 'format=json';
    }
    var old_hash = window.location.hash;
    if (old_hash) {
        window.location.hash = '';
    }
    $.getJSON(json_url(window.location.href), loaded);
});