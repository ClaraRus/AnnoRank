  var docTimes = {};  // Object to store view counts for each doc

  function viewDocTime(elementId, docId) {
    var docElement = document.getElementById(elementId);

      if (!(docId in docTimes)) {
          docTimes[docId] = [];
     }
    if (docElement.style.display === 'table-row'){
        var timestamp = new Date().getTime();
        docTimes[docId].push("start:" + timestamp);
    }
    else{
        var timestamp = new Date().getTime();
        docTimes[docId].push("stop:" + timestamp);
    }
  }



