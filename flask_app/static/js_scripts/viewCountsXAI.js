var docViews = {};  // Object to store view counts for each doc

function viewDocCount(elementId, docId, type = 'view') {
    if (!(docId in docViews)) {
        docViews[docId] = {view:0, view_factual: 0,  view_counterfactual: 0, view_image: 0, view_text: 0, view_image_text: 0};
    }

    docViews[docId][type]++;
}


