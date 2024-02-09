  var docViews = {};  // Object to store view counts for each doc

  function viewDocCount(elementId, docId) {
    var docElement = document.getElementById(elementId);

     if (!(docId in docViews)) {
          docViews[docId] = 0;  // Initialize view count if not exists
     }

    if (docElement.style.display === 'table-row'){
        docViews[docId]++;
    }
  }