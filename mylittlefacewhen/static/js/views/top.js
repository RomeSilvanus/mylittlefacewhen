// Generated by CoffeeScript 1.6.3
var ac_extractLast, ac_split;

window.TopView = Backbone.View.extend({
  el: $("#top"),
  initialize: function() {
    var _this = this;
    this.template = tpl.get("top");
    this.collection = new AdvertCollection();
    return KeyboardJS.on('s', null, function(event) {
      return $("#searchbar").focus();
    });
  },
  events: {
    "focus #topmenu a": "focused",
    "blur #topmenu a": "unfocused",
    "submit #search form": "search",
    "click #topmenu a": "navigateAnchor",
    "click #logo a": "navigateAnchor",
    "click #close-ad": "closeAd",
    "keydown input": "disableShortcuts",
    "keyup input": "disableShortcuts"
  },
  render: function() {
    $(this.el).html(this.template);
    this.autocomplete($("#searchbar"));
    return this;
  },
  closeAd: function(event) {
    event.preventDefault();
    $("#mainos").slideUp("fast");
    $.cookie('noads', true, {
      expires: 8,
      path: '/'
    });
    return void 0;
  },
  updateAd: function() {
    return;
    return void 0;
  },
  disableShortcuts: function(event) {
    return event.stopPropagation();
  },
  search: function(event) {
    var tags;
    event.preventDefault();
    tags = $("#searchbar").val();
    return app.navigate("/search/?tag=" + tags, {
      trigger: true
    });
  },
  focused: function(event) {
    return $(event.currentTarget.firstChild).addClass("focused");
  },
  unfocused: function(event) {
    return $(event.currentTarget.firstChild).removeClass("focused");
  },
  autocomplete: function(element) {
    return element.autocomplete({
      source: function(request, response) {
        var params;
        params = {
          name__contains: ac_extractLast(request.term),
          limit: 30
        };
        return $.getJSON("/api/v3/tag/", params, function(data, textStatus, jdXHR) {
          var d;
          d = [];
          _.each(data.objects, function(tag) {
            return d.push(tag.name);
          });
          return response(d, textStatus, jdXHR);
        });
      },
      search: function() {
        var term;
        term = ac_extractLast(this.value);
        if (term.length < 2) {
          return false;
        }
      },
      focus: function() {
        return false;
      },
      select: function(event, ui) {
        var terms;
        terms = ac_split(this.value);
        terms.pop();
        terms.push(ui.item.value);
        terms.push("");
        this.value = terms.join(", ");
        return false;
      }
    });
  }
});

ac_split = function(val) {
  return val.split(/,\s*/);
};

ac_extractLast = function(term) {
  return ac_split(term).pop();
};
