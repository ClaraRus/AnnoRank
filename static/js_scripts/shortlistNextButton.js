function collectDataShortlist(selection_range) {
      // Get all checkboxes with the name "item"
      var checkboxes = document.getElementsByName("shortlist");

      // Initialize an empty array to store selected items
      var selecteddocIds = [];

      // Loop through each checkbox and check if it's checked
      if (checkboxes.length > 0){
          for (var i = 0; i < checkboxes.length; i++) {
            console.log(checkboxes[i].checked)
            if (checkboxes[i].checked) {
              // If checked, add the value to the array
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
      fetch('/api/'+expId+'/get_next_task/')
        .then(response => response.json())
        .then(data => {
            // Handle the data in your JavaScript code
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

        // Check if doc_id is in docTimes
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
//       //Use jQuery AJAX to send data to the Flask app

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
        if (nextTask == 'done') {
            window.location.href = "/stop_experiment";
        } if (nextTask == 'form') {
            window.location.href ="/form"
            }
        else {
            // Redirect to the default link for other cases
            window.location.href = "/start_ranking/" + expId + "/index_ranking/" + nextTask +"/view";
        }
        },
        error: function(error) {
            console.log("Error:", error);
        }
          });
      } else {
        // Display a message to the user if less than three docs are selected
        alert("Please select at least " +selection_range[0] + " docs.");
      }
       })
        .catch(error => console.error('Error:', error));
    }