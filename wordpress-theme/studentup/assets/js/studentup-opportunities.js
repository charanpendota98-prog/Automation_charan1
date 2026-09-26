/* v123: active-opportunity finder — local filtering, no tracking or API calls. */
(function () {
  "use strict";
  var root = document.querySelector("[data-su-opportunities]");
  if (!root) return;
  var search = root.querySelector("[data-su-op-search]");
  var section = root.querySelector("[data-su-op-section-filter]");
  var qualification = root.querySelector("[data-su-op-qualification]");
  var deadline = root.querySelector("[data-su-op-deadline]");
  var result = root.querySelector("[data-su-op-results]");
  var empty = root.querySelector("[data-su-op-no-results]");
  var cards = Array.prototype.slice.call(root.querySelectorAll("[data-su-op-card]"));
  var groups = Array.prototype.slice.call(root.querySelectorAll(".su-op-section"));

  function apply() {
    var term = ((search && search.value) || "").trim().toLowerCase();
    var selectedSection = (section && section.value) || "";
    var selectedQualification = (qualification && qualification.value) || "";
    var selectedDeadline = (deadline && deadline.value) || "";
    var visible = 0;
    cards.forEach(function (card) {
      var title = card.getAttribute("data-su-op-title") || "";
      var cardSection = card.getAttribute("data-su-op-section") || "";
      var cardQualification = card.getAttribute("data-su-op-qual") || "";
      var daysRaw = card.getAttribute("data-su-op-days") || "unknown";
      var days = daysRaw === "unknown" ? null : parseInt(daysRaw, 10);
      var textOk = !term || title.indexOf(term) !== -1;
      var sectionOk = !selectedSection || cardSection === selectedSection;
      var qualificationOk = !selectedQualification || cardQualification.indexOf(selectedQualification) !== -1;
      var deadlineOk = !selectedDeadline ||
        (selectedDeadline === "unknown" ? days === null : days !== null && days >= 0 && days <= parseInt(selectedDeadline, 10));
      var show = textOk && sectionOk && qualificationOk && deadlineOk;
      card.hidden = !show;
      if (show) visible += 1;
    });
    groups.forEach(function (group) {
      var hasVisible = group.querySelector("[data-su-op-card]:not([hidden])");
      group.hidden = !hasVisible;
    });
    if (empty) empty.hidden = visible !== 0;
    if (result) result.textContent = visible + (visible === 1 ? " active update" : " active updates");
  }

  [search, section, qualification, deadline].forEach(function (control) {
    if (!control) return;
    control.addEventListener(control === search ? "input" : "change", apply);
  });
  apply();
})();
