let currentOpenItem_factual = null;
let currentOpenItem_counterfactual = null;
let currentOpenItem_image = null;
let currentOpenItem_text = null;
let currentOpenItem_image_text = null;
let currentOpenItem = null;
let currentOpenItem_updated = null;

function loadAndToggleVisibility(targetElementId, docId, htmlFile, type, close=true) {
    const targetElement = document.getElementById(targetElementId);
    const container = targetElement.querySelector("#injected-container");
    const isHidden = targetElement.style.display === 'none' || targetElement.style.display === '';

    const stateMap = {
        "view_factual": { get: () => currentOpenItem_factual, set: (val) => currentOpenItem_factual = val },
        "view_counterfactual": { get: () => currentOpenItem_counterfactual, set: (val) => currentOpenItem_counterfactual = val },
        "view_image": { get: () => currentOpenItem_image, set: (val) => currentOpenItem_image = val },
        "view_text": { get: () => currentOpenItem_text, set: (val) => currentOpenItem_text = val },
        "view_image_text": { get: () => currentOpenItem_image_text, set: (val) => currentOpenItem_image_text = val },
        "view": { get: () => currentOpenItem, set: (val) => currentOpenItem = val },
    };

    const currentState = stateMap[type];

    if (!currentState) {
        console.error(`STOPPING: The type "${type}" does not exist in stateMap. Please add it to viewDocInfoXAI.js!`);
        return;
    }

    if (isHidden) {
        fetch(htmlFile)
            .then(response => response.text())
            .then(data => {
                if (!container) {
                    targetElement.innerHTML = data;
                } else {
                    container.innerHTML = data;
                }

                if (targetElement.tagName.toLowerCase() === 'tr') {
                    targetElement.style.display = 'table-row';
                } else {
                    targetElement.style.display = 'block';
                }

                const prevOpen = currentState.get();
                if (prevOpen && prevOpen !== targetElement && close) {
                    const prevDocId = prevOpen.getAttribute('docid') || prevOpen.getAttribute('data-docid');
                    if (type !== 'updated') {
                        viewDocTime(prevDocId, type, "stop");
                    }
                    prevOpen.style.display = 'none';
                }

                if (type !== 'updated') {
                    viewDocCount(targetElementId, docId, type);
                    viewDocTime(docId, type, "start");
                }
                currentState.set(targetElement);
            })
            .catch(error => console.error("Error loading XAI content:", error));
    } else {
        targetElement.style.display = 'none';

        if (type !== 'updated') {
            viewDocTime(docId, type, "stop");
        }
        currentState.set(null);
    }
}