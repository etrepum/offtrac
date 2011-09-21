$(function () {
    var History = window.History;
    var TEMPLATE = {};
    var NOW = new Date();
    var CREOLE = new Parse.Simple.Creole({});

    $('script[type="text/x-mustache-template"]').each(function (idx, o) {
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

    function default_title(doc) {
        return doc.title + title_postfix;
    }
    
    var PAGES = {};
    PAGES.report = {
        title: function (doc) {
            return (doc.report_id ? '{' + doc.report_id + '} ' : '') + doc.title + title_postfix;
        },
        content: function (doc) {
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
            return {altlinks: "altlinks", content: "report"};
        }};
    PAGES.report_list = {
        content: function (doc) { return {content: 'report_list'}; }};
    PAGES.milestone_list = {
        content: function (doc) {
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
            return {content: "milestone_list"};
        }};
    PAGES.ticket = {
        title: function (doc) {
            var t = doc.ticket; 
            return '#' + t.id + ' ' + t.summary + title_postfix; },
        content: function (doc) {
            var t = doc.ticket;
            t.comments = group_comments(t.changes);
            /*
            TODO:

                Changes should be displayed as trac does it
                 * Description diff
            */
            
            return {content: "ticket"};
        }};
    PAGES.index = {
        content: function (doc) { return {content: "index"}; }};
    PAGES.timeline = {
        content: function (doc) {
            var tickets = doc.tickets;
            var comments = group_comments(doc.changes);
            doc.days = timeline_day_groups(comments, tickets);
            return {content: "timeline"};
        }};
    /*
    PAGES.search = {
    };
    */

    function strip_fragment(s) {
        return (s || '').replace(/#.*$/, '');
    }

    function enable_history(elem) {
        if (!History.enabled) {
            return;
        }
        var rootUrl = History.getRootUrl();
        var pageUrl = strip_fragment(document.location.href);
        function should_hook_history() {
            var url = this.href || '';
            return url && (url.substring(0, rootUrl.length) === rootUrl || url.indexOf(':') === -1);
        }
        $(elem).find("a:not(.no-ajaxy)").filter(should_hook_history).click(function (event) {
            // Continue as normal for cmd clicks and fragments
            if (event.which === 2 || event.metaKey || strip_fragment(this.href) === pageUrl) {
                return true;
            }
            load_url(this.href);
            event.preventDefault();
            return false;
        });
    }
    
    function render_doc(doc, opts) {
        doc.wiki_format = function () { return wiki_format };
        doc.change_format = function () { return change_format };
        doc.ago = function () { return ago_format; }
        $("div.use-mustache-template").each(function () {
            var template = opts[this.id],
                $this = $(this);
            if (template) {
                $this.html(Mustache.to_html(TEMPLATE[template], doc));
                enable_history($this);
            } else {
                $this.empty();
            }
        });
    }

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

    function decorate_closed_tickets(doc) {
        var ticket_num = /^\/ticket\/([a-fA-F0-9]+)/;
        var lst = doc.closed_tickets;
        function is_closed(n) {
            /* binary search */
            var high = lst.length - 1;
            var low = 0;
            while (high > low) {
                var mid = low + ((high - low) >> 1);
                var pair = lst[mid];
                var start = pair[0];
                if (n >= start) {
                    if (n <= (start + pair[1])) {
                        return true;
                    }
                    low = mid + 1;
                } else {
                    high = mid - 1;
                }
            }
            return false;
        }
        $("a[href^='/ticket/']").each(function () {
            var num = parseInt(ticket_num.exec(this.pathname)[1]);
            this.className += ' ticket' + (is_closed(num) ? ' closed' : '');
        });
    }

    function loaded(doc, url) {
        if (doc.user) {
            $("span.username").html(doc.user);
        }
        var page = PAGES[doc.template];
        var state = {content: {}, title: '', doc: doc, url: url};
        if (page) {
            state.title = (page.title ? page.title(doc) : default_title(doc));
        }
        return state;
    }
    
    function render_state(state) {
        var doc = state.doc;
        var page = PAGES[doc.template];
        render_doc(doc, (page ? page.content(doc): {}));
        $((document.location.hash || '').replace(':', '\\:')).each(function () {
            $("html, body").scrollTop($(this).offset().top);
        });
        $.getJSON(json_url('/closed_tickets'), decorate_closed_tickets);
    }

    function json_url(url) {
        url = url.split('#')[0];
        return url + (url.indexOf('?') === -1 ? '?' : '&') + 'format=json';
    }

    function load_url(url) {
        render_doc({}, {content: 'loading'});
        var xhr = $.getJSON(json_url(url)).pipe(function (doc) {
            return loaded(doc, url);
        });
        if (History.enabled) {
            xhr.done(function (state) {
                History.pushState(state, state.title, state.url);
            });
        } else {
            xhr.done(render_state);
        }
    }

    enable_history($(document.body));
    load_url(document.location.href);

    $(window).bind('statechange', function () {
        var state = History.getState();
        render_state(state.data);
    });
});