  var docCheckBox = [];  // Object to store view counts for each doc

  function orderCheckBox(checkbox, docId) {
    console.log(docId)
    if (checkbox.checked) {
        docCheckBox.push(docId)
    }

  }