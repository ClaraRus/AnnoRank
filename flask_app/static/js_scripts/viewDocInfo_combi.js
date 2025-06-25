let currentOpenItem_detail = null;
let currentOpenItem_cf = null;
let currentOpenItems_updated = {}; //As there can exist multiple updated buttons
let currentOpenItem_view = null;


function loadAndToggleVisibility(targetElementId, docId, htmlFile, type, updatedId=null, close=true) {//the close boolean controls whether to close the previous open item of the same type
    const targetElement = document.getElementById(targetElementId);
    console.log(targetElementId)

    const container = targetElement.querySelector("#injected-container");

    const isHidden = targetElement.style.display === 'none' || targetElement.style.display === '';

    if (isHidden) {
        fetch(htmlFile)
            .then(response => response.text())
            .then(data => {
                if (!container) {
                    targetElement.innerHTML = data;
                } else {
                    container.innerHTML = data;
                }

                targetElement.style.display = 'table-row';

                if (type === "view") {
                    // If another view is already open, close it
                    if (currentOpenItem_view && currentOpenItem_view !== targetElement && close) {
                        const prevDocId = currentOpenItem_view.getAttribute('docid');
                        viewDocTime(prevDocId, "view", "stop");
                        
                        // Also stop and hide detail nested in that view
                        if (currentOpenItem_detail && currentOpenItem_detail.getAttribute('docid') === prevDocId) {
                            viewDocTime(prevDocId, "detail", "stop");
                            currentOpenItem_detail.style.display = 'none';
                            currentOpenItem_detail = null;
                        }

                        currentOpenItem_view.style.display = 'none';
                        currentOpenItem_view = null;
                    }

                    viewDocCount(targetElementId, docId, "view");
                    viewDocTime(docId, "view", "start");
                    currentOpenItem_view = targetElement;

                } else if (type === "detail") {
                    if (currentOpenItem_detail && currentOpenItem_detail !== targetElement && close) {
                        const prevDocId = currentOpenItem_detail.getAttribute('docid');
                        viewDocTime(prevDocId, "detail", "stop");
                        currentOpenItem_detail.style.display = 'none';
                        currentOpenItem_detail = null;
                    }

                    viewDocCount(targetElementId, docId, "detail");
                    viewDocTime(docId, "detail", "start");
                    currentOpenItem_detail = targetElement;
                } else if (type === "cf") {
                    if (currentOpenItem_cf && currentOpenItem_cf !== targetElement && close) {
                        const prevDocId = currentOpenItem_cf.getAttribute('docid');
                        viewDocTime(prevDocId, "cf", "stop");
                        
                        // Also stop and hide any nested updated for the same docId
                        if (currentOpenItems_updated[prevDocId]) {
                            viewDocTime(prevDocId, "updated", "stop");
                            currentOpenItems_updated[prevDocId].style.display = 'none';
                            delete currentOpenItems_updated[prevDocId];
                        }

                        currentOpenItem_cf.style.display = 'none';
                        currentOpenItem_cf = null;
                    }

                    viewDocCount(targetElementId, docId, "cf");
                    viewDocTime(docId, "cf", "start");
                    currentOpenItem_cf = targetElement;
                } else if (type === "updated") {
                    if (currentOpenItems_updated[docId] && currentOpenItems_updated[docId] !== targetElement && close) {
                        const prevElement = currentOpenItems_updated[docId];
                        viewDocTime(docId, "updated", "stop");
                        prevElement.style.display = 'none';
                        delete currentOpenItems_updated[docId];
                    }

                    viewDocCount(targetElementId, docId, "updated", updatedId);
                    viewDocTime(docId, "updated", "start");

                    currentOpenItems_updated[docId] = targetElement;
                }
            })
            .catch(error => console.error(error));
    } else {
        // Hiding the element
        targetElement.style.display = 'none';

        if (type === "view") {
            viewDocTime(docId, "view", "stop");

            // Also stop and hide nested detail if open
            if (currentOpenItem_detail && currentOpenItem_detail.getAttribute('docid') === docId) {
                viewDocTime(docId, "detail", "stop");
                currentOpenItem_detail.style.display = 'none';
                currentOpenItem_detail = null;
            }


            currentOpenItem_view = null;

        } else if (type === "detail") {
            viewDocTime(docId, "detail", "stop");
            currentOpenItem_detail = null;
        } else if (type === "cf") {
            viewDocTime(docId, "cf", "stop");

            // Also stop and hide nested updated if open
            if (currentOpenItems_updated[docId]) {
                viewDocTime(docId, "updated", "stop");
                currentOpenItems_updated[docId].style.display = 'none';
                delete currentOpenItems_updated[docId];
            }
            
            currentOpenItem_cf = null;
        } else if (type === "updated") {
            viewDocTime(docId, "updated", "stop");
            delete currentOpenItems_updated[docId];
        }
    }
}

