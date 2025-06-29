var docTimes = {};  // Object to store timestamps for each doc

function viewDocTime(docId, type = 'view', action = 'start') {
    if (!(docId in docTimes)) {
        docTimes[docId] = { view: [], detail: [], cf: [], updated: [] }; // Initialize view count if not exists
    }

    const timestamp = new Date().getTime();
    docTimes[docId][type].push(`${action}:${timestamp}`); // Store the timestamp in the docTimes object
}
