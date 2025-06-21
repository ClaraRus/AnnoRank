let currentOpenItem_view = null;
let currentOpenItem_detail = null;

function loadAndToggleVisibility(targetElementId, docId, htmlFile, type) {
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
                console.log(data)
                targetElement.style.display = 'table-row';

                if (type === "view") {
                    // If another view is already open, close it
                    if (currentOpenItem_view && currentOpenItem_view !== targetElement) {
                        const prevDocId = currentOpenItem_view.getAttribute('docid');
                        viewDocTime(prevDocId, "view", "stop");

                        // Also stop any open detail row for that view
                        const detailRowId = `expandable-row-detail-${prevDocId}`;
                        const detailRow = document.getElementById(detailRowId);
                        if (detailRow && detailRow.style.display !== 'none') {
                            viewDocTime(prevDocId, "detail", "stop");
                            detailRow.style.display = 'none';
                            currentOpenItem_detail = null;
                        }

                        currentOpenItem_view.style.display = 'none';
                        currentOpenItem_view = null;
                    }

                    viewDocCount(targetElementId, docId, "view");
                    viewDocTime(docId, "view", "start");
                    currentOpenItem_view = targetElement;

                } else if (type === "detail") {
                    if (currentOpenItem_detail && currentOpenItem_detail !== targetElement) {
                        const prevDocId = currentOpenItem_detail.getAttribute('docid');
                        viewDocTime(prevDocId, "detail", "stop");
                        currentOpenItem_detail.style.display = 'none';
                        currentOpenItem_detail = null;
                    }

                    viewDocCount(targetElementId, docId, "detail");
                    viewDocTime(docId, "detail", "start");
                    currentOpenItem_detail = targetElement;
                }
            })
            .catch(error => console.error(error));
    } else {
        // Hiding the element
        targetElement.style.display = 'none';

        if (type === "view") {
            viewDocTime(docId, "view", "stop");

            // Also stop and hide detail if it's open
            const detailRowId = `expandable-row-detail-${docId}`;
            const detailRow = document.getElementById(detailRowId);
            if (detailRow && detailRow.style.display !== 'none') {
                viewDocTime(docId, "detail", "stop");
                detailRow.style.display = 'none';
                currentOpenItem_detail = null;
            }

            currentOpenItem_view = null;

        } else if (type === "detail") {
            viewDocTime(docId, "detail", "stop");
            currentOpenItem_detail = null;
        }
    }
}
