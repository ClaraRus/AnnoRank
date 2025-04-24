let currentOpenItem = null;


function loadAndToggleVisibility(targetElementId,docId, htmlFile) {
    const targetElement = document.getElementById(targetElementId);
    const container = targetElement.querySelector("#injected-container");

    console.log(targetElement)
    console.log(container)
    if (targetElement.style.display === 'none' || targetElement.style.display === '') {
        fetch(htmlFile)
            .then(response => response.text())
            .then(data => {
                console.log(data)
                console.log(targetElement)
                container.innerHTML = data;

                targetElement.style.display = 'table-row';
                // targetElement.style.display = '';
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
