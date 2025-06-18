var docViews = {};  // Object to store view counts for each doc

function viewDocCount(elementId, docId, type = 'view') {
    if (!(docId in docViews)) {
        docViews[docId] = { view: 0, detail: 0 };
    }

    docViews[docId][type]++;
}
