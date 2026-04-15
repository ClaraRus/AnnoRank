function collectDataShortlist(selection_range) {
      var checkboxes = document.getElementsByName("shortlist");

      var selecteddocIds = [];

      if (checkboxes.length > 0){
          for (var i = 0; i < checkboxes.length; i++) {
            if (checkboxes[i].checked) {
              selecteddocIds.push(checkboxes[i].getAttribute('ID'));

            }
          }
      }
      if(currentOpenItem !== null){
      if(currentOpenItem.style.display !== 'none'){
        currentOpenItem.style.display = 'none';
        viewDocTime(currentOpenItem.id, currentOpenItem.getAttribute('docid'))
      }
      }

      var element = document.getElementById('query_info');
      var queryId = element.getAttribute('qid');

      current_url = window.location.href;
      const expId = current_url.split('/')[4]
      const currentTask = current_url.split('/')[6]
      try{
      fetch('/api/'+expId+'/get_next_task/')
        .then(response => response.json())
        .then(data => {
            const nextTask = data.next_task;

            const interactions = {};

      var docs = document.getElementsByName("doc_row")
       for (var i = 0; i < docs.length; i++) {
        doc_id = docs[i].getAttribute('docid');
        const interactions_c = {};
        interactions_c['_doc_id'] = doc_id
        if (doc_id in docViews) {
            interactions_c['n_views'] = docViews[doc_id];
        } else {
            interactions_c['n_views'] = 0;
        }

        if (doc_id in docTimes) {
            interactions_c['timestamps'] = docTimes[doc_id];
        } else {
            interactions_c['timestamps'] = [];
        }
        if (checkboxes.length > 0){
            interactions_c['shortlisted'] = checkboxes[i].checked
        } else {
            interactions_c['shortlisted'] = null
        }
        interactions[doc_id] = interactions_c
      }

     if (selecteddocIds.length >= selection_range[0] && selecteddocIds.length <= selection_range[1]) {

      $.ajax({
        type: "POST",
        url: "/store_data_ranking",
        contentType: "application/json;charset=UTF-8",
        data: JSON.stringify({ selectedItems: selecteddocIds ,
        viewCounts: docViews,
        viewTimes: docTimes,
        orderCheckBox: docCheckBox,
        interactions: interactions,
        queryId: queryId,
        expId: expId,
        nTask: currentTask
        }),
        success: function(response) {

        // Get the current URL
        if (nextTask == 'stop_experiment') {
            window.location.href = "/stop_experiment";
        } if (nextTask == 'form') {
            window.location.href ="/form"
            }
        else {
            window.location.href = "/start_ranking/" + expId + "/index_ranking/" + nextTask +"/view";
        }
        },
        error: function(error) {
            console.log("Error:", error);
        }
          });
      } else {
        alert("Please select at least " +selection_range[0] + " docs.");
      }
       })
        .catch(error => console.error('Error:', error));
        } catch (error) {
        console.error('Error fetching next task:', error);
        alert('Failed to fetch next task.');
      }
    }