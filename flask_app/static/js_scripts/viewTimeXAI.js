var docTimes = {};  // Object to store timestamps for each doc

function viewDocTime(docId, type = 'view', action = 'start') {
    if (!(docId in docTimes)) {
        docTimes[docId] = { view: [], view_factual: [], view_counterfactual: [], view_image: [], view_text: [],  view_image_text: []};
    }

    const timestamp = new Date().getTime();
    docTimes[docId][type].push(`${action}:${timestamp}`);
}


