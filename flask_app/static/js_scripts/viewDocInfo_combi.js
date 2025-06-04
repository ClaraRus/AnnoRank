let currentOpenItem_detail = null;
let currentOpenItem_cf = null;
let currentOpenItem_updated = null;
let currentOpenItem_view = null;


function loadAndToggleVisibility(targetElementId, docId, htmlFile, type, close=false) {//the close boolean controls whether to close the previous open item of the same type
    const targetElement = document.getElementById(targetElementId);

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
                        // viewDocTime(prevDocId, "view", "stop");

                        // Also stop any open detail row for that view
                        // const detailRowId = `expandable-row-detail-${prevDocId}`;
                        // const detailRow = document.getElementById(detailRowId);
                        // if (detailRow && detailRow.style.display !== 'none') {
                        //     // viewDocTime(prevDocId, "detail", "stop");
                        //     detailRow.style.display = 'none';
                        //     currentOpenItem_detail = null;
                        // }

                        currentOpenItem_view.style.display = 'none';
                        currentOpenItem_view = null;
                    }

                    // viewDocCount(targetElementId, docId, "view");
                    // viewDocTime(docId, "view", "start");
                    currentOpenItem_view = targetElement;

                } else if (type === "detail") {
                    if (currentOpenItem_detail && currentOpenItem_detail !== targetElement && close) {
                        const prevDocId = currentOpenItem_detail.getAttribute('docid');
                        // viewDocTime(prevDocId, "detail", "stop");
                        currentOpenItem_detail.style.display = 'none';
                        currentOpenItem_detail = null;
                    }

                    // viewDocCount(targetElementId, docId, "detail");
                    // viewDocTime(docId, "detail", "start");
                    currentOpenItem_detail = targetElement;
                } else if (type === "cf") {
                    if (currentOpenItem_cf && currentOpenItem_cf !== targetElement && close) {
                        const prevDocId = currentOpenItem_cf.getAttribute('docid');
                        // viewDocTime(prevDocId, "cf", "stop");

                        currentOpenItem_cf.style.display = 'none';
                        currentOpenItem_cf = null;
                    }

                    // viewDocCount(targetElementId, docId, "cf");
                    // viewDocTime(docId, "cf", "start");
                    currentOpenItem_cf = targetElement;
                } else if (type === "updated") {
                    console.log("Updated view opened for docId:", docId);
                    console.log("Current open updated item:", currentOpenItem_updated);
                    console.log("Target element:", targetElement);
                    if (currentOpenItem_updated && currentOpenItem_updated !== targetElement && close) {
                        // console.log("Closing previous updated view for docId:", currentOpenItem_updated.getAttribute('docid'));
                        const prevDocId = currentOpenItem_updated.getAttribute('docid');
                        // viewDocTime(prevDocId, "updated", "stop");
                        currentOpenItem_updated.style.display = 'none';
                        currentOpenItem_updated = null;
                    }

                    // viewDocCount(targetElementId, docId, "updated");
                    // viewDocTime(docId, "updated", "start");
                    currentOpenItem_updated = targetElement;
                    console.log("Current open updated item set to:", currentOpenItem_updated);
                }
            })
            .catch(error => console.error(error));
    } else {
        // Hiding the element
        targetElement.style.display = 'none';

        if (type === "view") {
            // viewDocTime(docId, "view", "stop");

            // Also stop and hide detail if it's open
            // const detailRowId = `expandable-row-detail-${docId}`;
            // const detailRow = document.getElementById(detailRowId);
            // if (detailRow && detailRow.style.display !== 'none') {
            //     // viewDocTime(docId, "detail", "stop");
            //     detailRow.style.display = 'none';
            //     currentOpenItem_detail = null;
            // }

            currentOpenItem_view = null;

        } else if (type === "detail") {
            // viewDocTime(docId, "detail", "stop");
            currentOpenItem_detail = null;
        } else if (type === "cf") {
            // viewDocTime(docId, "cf", "stop");
            
            currentOpenItem_cf = null;
        } else if (type === "updated") {
            // viewDocTime(docId, "updated", "stop");
            currentOpenItem_updated = null;
        }
    }
}

