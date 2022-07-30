var abortController;

const csrf_token = document.querySelector('input[name="csrf_token"]').value;
let autoCompleteTimeoutId = undefined;

function init_tagify(field, relatedModelName) {
    const tagify = new Tagify(field, {
        dropdown: {mapValueTo: 'searchBy'},
        tagTextProp: 'searchBy',
    });
    tagify.on('input', e => {onInput(tagify, relatedModelName, e.detail.value)});
}

function onInput(tagify, modelName, userInput) {
    if (autoCompleteTimeoutId !== undefined) {
        clearTimeout(autoCompleteTimeoutId);
    }
    autoCompleteTimeoutId = setTimeout(function() {
        databaseSearch(tagify, modelName, userInput);
    }, 250);
}

function databaseSearch(tagify, modelName, userInput) {
  tagify.whitelist = null; // reset the whitelist

  abortController && abortController.abort();
  abortController = new AbortController();
  tagify.loading(true).dropdown.hide();
  const url = '/entries/search/regex/' + modelName + '?q=' + userInput;
  const options = {signal: abortController.signal, headers: new Headers({'X-CSRFToken': csrf_token})};
  fetch(url, options)
    .then(RES => RES.json())
    .then(function(results) {
      // map the entires in the newWhitelist
      // remove the _id field and a value field consisting of all the fields concatenated
      let whitelist = results.entries.map(entry => {
        const compoundId = modelName + '/' + entry._id['$oid'];
        const label = entry['_to_string'];
        return {'searchBy': label, 'value': compoundId};
      });
      tagify.whitelist = whitelist; // update whitelist Array in-place
      tagify.settings.enforceWhitelist = true;
      tagify.loading(false).dropdown.show(userInput) // render the suggestions dropdown
    });
}