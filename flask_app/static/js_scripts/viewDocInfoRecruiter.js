let currentOpenItem_view = null;
let currentOpenItem_cf = null;

function loadAndToggleVisibility(targetElementId, docId, htmlFile, type = "view") {
    const targetElement = document.getElementById(targetElementId);

    if (targetElement.style.display === 'none' || targetElement.style.display === '') {
        fetch(htmlFile)
            .then(response => response.text())
            .then(data => {
                targetElement.innerHTML = data;
                targetElement.style.display = 'table-row';

                if (type === "view") {
                    if (currentOpenItem_view && currentOpenItem_view !== targetElement) {
                        currentOpenItem_view.style.display = 'none';
                        viewDocTime(currentOpenItem_view.id, currentOpenItem_view.getAttribute('cid'));
                    }
                    currentOpenItem_view = targetElement;
                    viewDocCount(targetElementId, docId);
                    viewDocTime(targetElementId, docId);

                } else if (type === "cf") {
                    if (currentOpenItem_cf && currentOpenItem_cf !== targetElement) {
                        currentOpenItem_cf.style.display = 'none';
                    }
                    currentOpenItem_cf = targetElement;
                }
            })
            .catch(error => console.error(error));
    } else {
        targetElement.style.display = 'none';

        if (type === "view") {
            viewDocTime(targetElementId, docId);
            currentOpenItem_view = null;
        } else if (type === "cf") {
            currentOpenItem_cf = null;
        }
    }
}
