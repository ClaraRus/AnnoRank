function collectDataShortlist(selection_range, expId, currentTask) {
    const checkboxes = document.getElementsByName("shortlist");
    const selecteddocIds = [];

    if (checkboxes.length > 0) {
        for (let i = 0; i < checkboxes.length; i++) {
            if (checkboxes[i].checked) {
                selecteddocIds.push(checkboxes[i].getAttribute('ID'));
            }
        }
    }

    const categories = [
        { element: typeof currentOpenItem_factual !== 'undefined' ? currentOpenItem_factual : null, type: "view_factual" },
        { element: typeof currentOpenItem_counterfactual !== 'undefined' ? currentOpenItem_counterfactual : null, type: "view_counterfactual" },
        { element: typeof currentOpenItem_image !== 'undefined' ? currentOpenItem_image : null, type: "view_image" },
        { element: typeof currentOpenItem_text !== 'undefined' ? currentOpenItem_text : null, type: "view_text" },
        { element: typeof currentOpenItem_image_text !== 'undefined' ? currentOpenItem_image_text : null, type: "view_image_text" },
        { element: typeof currentOpenItem !== 'undefined' ? currentOpenItem : null, type: "view" }
    ];

    categories.forEach(cat => {
        const openEl = cat.element;
        if (openEl && openEl.style.display !== 'none') {
            const docId = openEl.getAttribute('docid') || openEl.getAttribute('data-docid');

            if (docId && typeof viewDocTime === 'function') {
                viewDocTime(docId, cat.type, "stop");
                openEl.style.display = 'none';
            }
        }
    });

    const element = document.getElementById('query_info');
    const queryId = element ? element.getAttribute('qid') : "";

    try {
        fetch(window.FLASK_URLS.get_next_task)
            .then(response => response.json())
            .then(data => {
                const nextTask = data.next_task;

                if (selecteddocIds.length >= selection_range[0] && selecteddocIds.length <= selection_range[1]) {

                    const interactionsPayload = {};
                    const views = typeof docViews !== 'undefined' ? docViews : {};
                    const times = typeof docTimes !== 'undefined' ? docTimes : {};

                    const allDocIds = new Set([...Object.keys(views), ...Object.keys(times)]);

                    allDocIds.forEach(docId => {
                        interactionsPayload[docId] = {};
                        const docView = views[docId] || {};
                        const docTime = times[docId] || {};

                        const types = ['view', 'view_factual', 'view_counterfactual', 'view_image', 'view_text', 'view_image_text'];
                        types.forEach(type => {
                            interactionsPayload[docId][type] = docView[type] || 0;
                            interactionsPayload[docId][type + '_timestamps'] = docTime[type] || [];
                        });
                    });

                    $.ajax({
                        type: "POST",
                        url: window.FLASK_URLS.store_data_ranking,
                        contentType: "application/json;charset=UTF-8",
                        data: JSON.stringify({
                            selectedItems: selecteddocIds,
                            orderCheckBox: typeof docCheckBox !== 'undefined' ? docCheckBox : [],
                            interactions: interactionsPayload,
                            queryId: queryId,
                            expId: expId,
                            nTask: currentTask
                        }),
                        success: function (response) {
                            if (typeof window.docViews !== 'undefined') window.docViews = {};
                            if (typeof window.docTimes !== 'undefined') window.docTimes = {};

                            if (nextTask === 'stop_experiment') {
                                window.location.href = window.FLASK_URLS.stop_experiment;
                            } else {
                                window.location.href = window.FLASK_URLS.questionnaire;
                            }
                        },
                        error: function (error) {
                            console.error("AJAX Error:", error);
                        }
                    });
                } else {
                    alert("Please select " + selection_range[0] + " candidates to proceed.");
                }
            })
            .catch(error => console.error('Error fetching next task:', error));
    } catch (error) {
        console.error('Workflow error:', error);
    }
}