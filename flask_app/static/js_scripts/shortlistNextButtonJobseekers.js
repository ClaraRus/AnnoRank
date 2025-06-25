function collectDataShortlist(selection_range) {
      // Get all checkboxes with the name "item"
      var checkboxes = document.getElementsByName("shortlist");

      // Initialize an empty array to store selected items
      var selecteddocIds = [];

      // Loop through each checkbox and check if it's checked
      if (checkboxes.length > 0){
          for (var i = 0; i < checkboxes.length; i++) {
            if (checkboxes[i].checked) {
              // If checked, add the value to the array
              selecteddocIds.push(checkboxes[i].getAttribute('ID'));

            }
          }
      }
      if (currentOpenItem_view !== null && currentOpenItem_view.style.display !== 'none') {
          currentOpenItem_view.style.display = 'none';
          viewDocTime(currentOpenItem_view.getAttribute('docid'), "view", "stop");
      }
      
      if (currentOpenItem_cf !== null && currentOpenItem_cf.style.display !== 'none') {
          currentOpenItem_cf.style.display = 'none';
          viewDocTime(currentOpenItem_cf.getAttribute('docid'), "cf", "stop");
      }

    //   if (currentOpenItem_updated !== null && currentOpenItem_updated.style.display !== 'none') {
    //       currentOpenItem_updated.style.display = 'none';
    //       viewDocTime(currentOpenItem_updated.getAttribute('docid'), "updated", "stop");
    //   }

      for (const docId in currentOpenItems_updated) {
        const element = currentOpenItems_updated[docId];
        if (element && element.style.display !== 'none') {
            element.style.display = 'none';
            viewDocTime(docId, "updated", "stop");
        }
      }
      currentOpenItems_updated = {};
      
      if (currentOpenItem_detail !== null && currentOpenItem_detail.style.display !== 'none') {
          currentOpenItem_detail.style.display = 'none';
          viewDocTime(currentOpenItem_detail.getAttribute('docid'), "detail", "stop");
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
            // Handle the data in your JavaScript code
            const nextTask = data.next_task;

            const interactions = {};

      var docs = document.getElementsByName("doc_row")
       for (var i = 0; i < docs.length; i++) {
        doc_id = docs[i].getAttribute('docid');
        const interactions_c = {};
        interactions_c['_doc_id'] = doc_id


        // Button counts
        interactions_c['view_n'] = (docViews[doc_id] && docViews[doc_id].view) ? docViews[doc_id].view : 0;
        interactions_c['detail_n'] = (docViews[doc_id] && docViews[doc_id].detail) ? docViews[doc_id].detail : 0;
        interactions_c['cf_n'] = (docViews[doc_id] && docViews[doc_id].cf) ? docViews[doc_id].cf : 0;
        interactions_c['updated_n'] = (docViews[doc_id] && docViews[doc_id].updated) ? docViews[doc_id].updated : {};
    
        // Timestamps
        interactions_c['view_timestamps'] = (docTimes[doc_id] && docTimes[doc_id].view) ? docTimes[doc_id].view : [];
        interactions_c['detail_timestamps'] = (docTimes[doc_id] && docTimes[doc_id].detail) ? docTimes[doc_id].detail : [];
        interactions_c['cf_timestamps'] = (docTimes[doc_id] && docTimes[doc_id].cf) ? docTimes[doc_id].cf : [];
        interactions_c['updated_timestamps'] = (docTimes[doc_id] && docTimes[doc_id].updated) ? docTimes[doc_id].updated : [];


        if (checkboxes.length > 0) {
            // Find the checkbox for this specific doc (using index + 1 since checkboxes are 1-indexed)
            const checkbox = document.getElementById((i + 1).toString());
            interactions_c['shortlisted'] = checkbox ? checkbox.checked : false;
        } else {
            interactions_c['shortlisted'] = null;
        }
        interactions[doc_id] = interactions_c
      }

    //  if (selecteddocIds.length >= selection_range[0] && selecteddocIds.length <= selection_range[1]) {
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
      if (nextTask == 'stop_experiment') {
          window.location.href = "/stop_experiment";
      } //if (nextTask == 'form') {
        //  window.location.href ="/form"
        //  }
      else {
          // Redirect to the default link for other cases
          //window.location.href = "/start_ranking_recruiter/" + expId + "/index_ranking/" + nextTask +"/view";
          window.location.href = "/questionnaire/" + expId +  "/" + currentTask;

      }
      },
      error: function(error) {
          console.log("Error:", error);
      }
        });
    // } else {
    //   // Display a message to the user if less than three docs are selected
    //   alert("Please select at least " +selection_range[0] + " docs.");
    // }
     })
      .catch(error => console.error('Error:', error));
      } catch (error) {
      console.error('Error fetching next task:', error);
      alert('Failed to fetch next task.');
      // Optionally, update the UI to show an error message
    }
  }