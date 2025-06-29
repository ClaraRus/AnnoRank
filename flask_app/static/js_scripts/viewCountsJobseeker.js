var docViews = {};  // Object to store view counts for each doc

function viewDocCount(elementId, docId, type = 'view', updatedId = null) {
    if (!(docId in docViews)) {
        docViews[docId] = { view: 0, detail: 0, cf: 0, updated: {} }; // Initialize view count if not exists
    }
    if (type === 'updated') { // Handle updated views separately due to multiple buttons
        if (!(updatedId in docViews[docId].updated)) {
            docViews[docId].updated[updatedId] = 0; // Initialize view count if not exists
        }
        docViews[docId].updated[updatedId]++;
    } else {
        docViews[docId][type]++;
    }
}
