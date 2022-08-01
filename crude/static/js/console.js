
class Console extends HTMLElement {
    constructor() {
        super();
        this.attachShadow({ mode: 'open' });
        this.csrf_token = document.querySelector('input[name="csrf_token"]').value;
        const template = this.getTemplate();
        this.shadowRoot.appendChild(template.content.cloneNode(true));

        this.domNodes = {
            commandLine: this.shadowRoot.getElementById('command-line'),
            matchList: this.shadowRoot.getElementById('matchlist'),
            input: undefined
        };
        this.globalEventListeners = [];
        this.lastSearchTerm = undefined;
        this.selectedIndex = undefined;
        this.lastNavigationSearchTerm = undefined;

        this.abortController = new AbortController();

        this.autoCompleteTimeoutId = undefined;
        this.modelNames = [];
        this.currentSearchResults = {};
        this.loadModelNames();
    }
    connectedCallback() {
        this.registerEventListeners();
    }
    loadModelNames() {
        var self = this;
        const dataList = document.getElementById(this.getAttribute('data-list'));
        const options = dataList.querySelectorAll('option');
        options.forEach(function(option) {
            self.modelNames.push(option.innerText);
        });
    }
    cmdLineIsVisible() { return this.style.display === 'block'; }
    matchListIsVisible() { return this.domNodes.matchList.style.display === 'block'; }
    isInputInBackground() { return this.domNodes.input !== undefined; }
    registerEventListeners() {
        var self = this;
        document.addEventListener('keydown', function(e) {
            // detect if control space was pressed
            if (e.keyCode === 32 && e.ctrlKey) {
                if (self.cmdLineIsVisible()) {
                    self.hideCmdLine();
                }
                else {
                    self.domNodes['input'] = undefined;
                    if (document.activeElement.tagName === 'INPUT') {
                        self.domNodes['input'] = document.activeElement;
                    }

                    self.showCmdLine();
                }
            }
            // detect escape
            if (e.keyCode === 27) {
                self.hideCmdLine();
            }
        });
        this.domNodes.commandLine.addEventListener('keydown', this.keydownHandler.bind(this));
        this.domNodes.commandLine.addEventListener('keyup', this.keyupHandler.bind(this));
    }
    hideMatchList() {
        this.abortController.abort();
        this.lastSearchTerm = undefined;
        this.lastNavigationSearchTerm = undefined;
        this.selectedIndex = undefined;
        this.domNodes.matchList.style.display = 'none';
    }
    matchNavigation(userInput) {
        var self = this;
        if (this.lastNavigationSearchTerm === userInput) {
            return;
        }
        // split user input into words
        const words = userInput.split(' ');
        const actions = ['browse', 'edit'];
        const modelNames = this.modelNames;
        // check if the user input matches a quick url
        // by checking each word against the actions and model names
        let foundActions = [];
        let foundModels = [];
        words.forEach(function(word) {
            // find which action matches the word
            foundActions = foundActions.concat(actions.filter(function(action) {
                return action.includes(word);
            }));
            // find which model matches the word
            foundModels = foundModels.concat(modelNames.filter(function(modelName) {
                return modelName.includes(word);
            }));
        });
        this.lastNavigationSearchTerm = userInput;
        this.currentSearchResults['navigation'] = [];
        if (foundActions.length == 0 && foundModels.length == 0) {
            // no action and no model is matching..
            return;
        }
        let matchedModels = foundModels;
        let matchedActions = foundActions;
        if (foundModels.length == 0) {
            matchedModels = modelNames;
        }
        if (foundActions.length == 0) {
            matchedActions = actions;
        }

        matchedModels.forEach(function(modelName) {
            matchedActions.forEach(function(action) {
                const actionUrl = '/entries/' + action + '/' + modelName;
                const searchEntry = {
                    url: actionUrl,
                    label: action + '->' + modelName
                };
                self.currentSearchResults['navigation'].push(searchEntry);
            });
        });
        this.renderSearchResults();
    }
    renderSearchResults() {
        var self = this;
        this.domNodes.matchList.innerHTML = '';
        Object.keys(this.currentSearchResults).forEach(function(modelName) {
            if (self.currentSearchResults[modelName].length > 0) {
                const separator = document.createElement('div');
                separator.textContent = modelName;
                separator.classList.add('separator');
                self.domNodes.matchList.appendChild(separator);
            }
            self.currentSearchResults[modelName].forEach(function(searchEntry) {
                const match = document.createElement('div');
                match.setAttribute('data-url', searchEntry.url);
                match.setAttribute('data-id', searchEntry.id);
                match.textContent = searchEntry.label;
                self.domNodes.matchList.appendChild(match);
            });
        });
        if (this.selectedIndex !== undefined) {
            // select the item at the selected index
            this.domNodes.matchList.childNodes[this.selectedIndex].classList.add('selected');
        }
        this.domNodes.matchList.style.display = 'block';
    }
    addSearchResults(searchTerm, modelName, searchResults) {
        var self = this;
        // append the entries to the current search results
        // check if the searchterm still matches the input in the command-line
        this.currentSearchResults[modelName] = [];
        if (searchResults.entries.length > 0 && searchTerm === this.domNodes.commandLine.value) {
            searchResults.entries.forEach(function(entry) {
                // add url to entry
                const compoundId = modelName + '/' + entry._id["$oid"];
                const actionUrl = '/entries/read/' + compoundId;
                const label = entry['_to_string'];
                const searchEntry = {
                    url: actionUrl,
                    label: label,
                    id: compoundId
                };
                self.currentSearchResults[modelName].push(searchEntry);
            });
        }
        this.renderSearchResults();
    }
    databaseSearch(userInput) {
        var self = this;
        if (userInput === this.lastSearchTerm) {
            return;
        }
        this.modelNames.forEach(function(modelName) {
            self.currentSearchResults[modelName] = [];
        });
        this.abortController.abort();
        this.abortController = new AbortController();
        this.lastSearchTerm = userInput;
        self.modelNames.forEach(function(modelName) {
            const url = '/entries/search/regex/' + modelName + '?q=' + userInput;
            const options = {signal: self.abortController.signal, headers: new Headers({'X-CSRFToken': self.csrf_token})};
            fetch(url, options).then(function(response) {
                response.json().then(function(data) {
                    self.addSearchResults(userInput, modelName, data);
                });
            }).catch(error => {
                console.log(error);
            });
        });
        this.autoCompleteTimeoutId = undefined;
    }
    processCommand(userInput) {
        console.log('processCommand: ' + userInput);
    }
    gotoItem(selectedItem) {
        const url = selectedItem.getAttribute('data-url');
        window.location.href = url;
    }
    insertItem(selectedItem) {
        const itemId = selectedItem.getAttribute('data-id', false);
        const itemLabel = selectedItem.textContent;
        // insert the item into the input in the background
        this.domNodes.input.value += itemId + '(' + itemLabel + ')';
        this.hideCmdLine();
    }
    letterReceived(userInput) {
        var self = this;
        if (this.autoCompleteTimeoutId !== undefined) {
            clearTimeout(this.autoCompleteTimeoutId);
        }
        this.autoCompleteTimeoutId = setTimeout(function() {
            self.databaseSearch(userInput);
        }, 250);
    }
    keydownHandler(event) {
        const matchesVisible = this.matchListIsVisible();
        if (event.which === 38) { // 38 = up
            if (matchesVisible) this.selectionUp();
            event.preventDefault();
            event.stopPropagation();
            return;
        }
        else if (event.which === 40) { // 40 = down
            if (matchesVisible) this.selectionDown();
            event.preventDefault();
            event.stopPropagation();
            return;
        }
        else if (event.which === 13 && this.selectedIndex !== undefined) { // 13 = enter
            if (matchesVisible) {
                const selectedItem = this.domNodes.matchList.childNodes[this.selectedIndex];
                if (event.shiftKey && this.isInputInBackground()) {
                    this.insertItem(selectedItem);
                } else {
                    this.gotoItem(selectedItem);
                }
            }
            event.preventDefault();
            return;
        }
    }
    keyupHandler(event) {
        if (!this.cmdLineIsVisible()) {
            return;
        }
        if (event.which === 27) {  // 27 = esc
            this.hideCmdLine();
            event.preventDefault();
            return;
        }
        const userInput = this.domNodes.commandLine.value.trim();

        if (userInput.length > 2) {
            this.letterReceived(userInput);
            this.matchNavigation(userInput);
        }
        else {
            this.hideMatchList();
        }
    }
    selectionUp() {
        if (this.selectedIndex !== undefined) {
            this.domNodes.matchList.children[this.selectedIndex].classList.remove('selected');
        }
        if (this.selectedIndex === undefined || this.selectedIndex === 1) {
            this.selectedIndex = this.domNodes.matchList.childNodes.length - 1;
        }
        else if (this.domNodes.matchList.childNodes[this.selectedIndex - 1].classList.contains('separator')) {
            this.selectedIndex -= 2;
        }
        else {
            this.selectedIndex--;
        }
        this.domNodes.matchList.childNodes[this.selectedIndex].classList.add('selected');
    }
    selectionDown() {
        if (this.selectedIndex !== undefined) {
            this.domNodes.matchList.children[this.selectedIndex].classList.remove('selected');
        }
        if (this.selectedIndex === undefined || this.selectedIndex === this.domNodes.matchList.childNodes.length - 1) {
            this.selectedIndex = 1;
        }
        else if (this.domNodes.matchList.childNodes[this.selectedIndex + 1].classList.contains('separator')) {
            this.selectedIndex += 2;
        }
        else {
            this.selectedIndex++;
        }

        this.domNodes.matchList.childNodes[this.selectedIndex].classList.add('selected');
    }

    showCmdLine() {
        if (typeof removeQuickKeys === 'function') {
            removeQuickKeys();
        }
        this.style.display = 'block';
        this.shadowRoot.getElementById('command-line').focus();
    }
    hideCmdLine() {
        this.hideMatchList();
        this.style.display = 'none';
        this.domNodes.commandLine.value = '';
        if (this.domNodes.input !== undefined) {
            this.domNodes.input.focus();
            this.domNodes.input = undefined;
        }
        if (typeof attachQuickKeys === 'function') {
            attachQuickKeys();
        }
    }
    getTemplate() {
        const template = document.createElement('template');
        template.innerHTML = `<style>
                                .selected {
                                  background-color: #1095c1;
                                  color: white;
                                }
                                .separator {
                                  color: gray;
                                  font-size: x-small;
                                  border-top: 1px solid gray;
                                }
                                #command-line-wrapper {
                                    position: absolute;
                                    margin: 0 auto;
                                    top: 25%;
                                    left: 0;
                                    right: 0;
                                    width: 60%;
                                    min-width: 15em;
                                    max-width: 40em;
                                    z-index: 999;
                                    padding: 0.5em calc(0.5em + 4px) 0.5em 0.5em;
                                    background-color: #333;
                                    /* add rounded corners */
                                    border-radius: 0.2em;
                                }

                                #command-line-wrapper > #command-line {
                                    width: 100%;
                                    height: 2em;
                                    padding: 0;
                                    margin: 0;
                                }

                                #matchlist {
                                    display: none;
                                    max-height: 25em;
                                    overflow-x: hidden;
                                    overflow-y: auto;
                                }

                                #matchlist > div {
                                    padding: 6px;
                                    border-radius: 0.2em;
                                }
                            </style>
                            <div id="command-line-wrapper">
                                <input type="text" id="command-line" placeholder="Search" />
                                <div id="matchlist"></div>
                            </div>`;
        return template;
    }
}


window.customElements.define('command-line', Console);