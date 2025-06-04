var docTimes = {};  // Object to store timestamps for each doc

function viewDocTime(docId, type = 'view', action = 'start') {
    if (!(docId in docTimes)) {
        docTimes[docId] = { view: [], detail: [] };
    }

    const timestamp = new Date().getTime();
    docTimes[docId][type].push(`${action}:${timestamp}`);
}
