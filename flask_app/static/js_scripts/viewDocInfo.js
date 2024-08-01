let currentOpenItem = null;


function loadAndToggleVisibility(targetElementId,docId, htmlFile) {
    const targetElement = document.getElementById(targetElementId);
    if (targetElement.style.display === 'none' || targetElement.style.display === '') {
        fetch(htmlFile)
            .then(response => response.text())
            .then(data => {
                targetElement.innerHTML = data;
                targetElement.style.display = 'table-row';

                  if (currentOpenItem && currentOpenItem !== targetElement) {
                    currentOpenItem.style.display = 'none';
                    viewDocTime(currentOpenItem.id, currentOpenItem.getAttribute('cid'))
                    currentOpenItem = null;

                  }
                 viewDocCount(targetElementId, docId)
                 viewDocTime(targetElementId, docId)
                 if (targetElement.style.display == 'table-row'){
                    currentOpenItem = targetElement;
                 }
                 else{
                    currentOpenItem = null;
                 }

            })
            .catch(error => console.error(error));
    } else {
        targetElement.style.display = 'none';
        viewDocTime(targetElementId, docId)
        currentOpenItem = null;

    }




}
