function nextButton(direction) {
      current_url = window.location.href;
      const expId = current_url.split('/')[4]
      const currentTask = current_url.split('/')[6]


      fetch('/api/'+expId+'/get_task/'+direction+'/'+currentTask)
      .then(response => response.json())
      .then(response => {
        const nextTask = response.next_task;


     if (1) {
//       //Use jQuery AJAX to send data to the Flask app

      $.ajax({
        type: "POST",
        contentType: "application/json;charset=UTF-8",
        data: JSON.stringify({
        expId: expId,
        nTask: currentTask
        }),
        success: function(response) {
        console.log("Success:", response);

        // Get the current URL
        if (nextTask == 'done') {
            window.location.href = "/stop_experiment";
        } else {
            // Redirect to the default link for other cases
            window.location.href = "/start_compare/" + expId + "/index_compare/" + nextTask ;
        }
        },
        error: function(error) {
            console.log("Error:", error);
        }
          });
      } else {
        // Display a message to the user if less than three docs are selected
        alert("Please select three docs.");
      }
       })
        .catch(error => console.error('Error:', error));
    }


   function nextButtonAnnotateCompare() {
      current_url = window.location.href;
      const expId = current_url.split('/')[4]
      const currentTask = current_url.split('/')[6]


      var rankings = document.getElementsByName("ranking_table")
      var  ranking_type_1 = rankings[0].getAttribute('id');
      var  ranking_type_2 = rankings[1].getAttribute('id');

      var checkbox_1 = document.getElementById('shortlist_1');
      var checkbox_2 = document.getElementById('shortlist_2');
        console.log(checkbox_1)

      var selected_ranking = ""

      if (checkbox_2.checked) {
            selected_ranking = ranking_type_2
        }
      else{
            if (checkbox_1.checked)
                selected_ranking = ranking_type_1
      }
   try{
      fetch('/api/'+expId+'/get_next_task/')
      .then(response => response.json())
      .then(response => {
        const nextTask = response.next_task;


     if (selected_ranking !== "") {
//       //Use jQuery AJAX to send data to the Flask app

      $.ajax({
        type: "POST",
        contentType: "application/json;charset=UTF-8",
        url: "/store_data_compare_ranking",
        data: JSON.stringify({
        selected_ranking: selected_ranking,
        ranking_type_1: ranking_type_1,
        ranking_type_2: ranking_type_2,
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
            // Redirect to the default link for other cases
            window.location.href = "/start_compare_annotate/" + expId + "/index_compare_annotate/" + nextTask ;
        }
        },
        error: function(error) {
            console.log("Error:", error);
        }
          });
      } else {
        alert("Please select a ranking.");
      }
       })
        .catch(error => console.error('Error:', error));
      } catch (error) {
        console.error('Error fetching next task:', error);
        alert('Failed to fetch next task.');
        // Optionally, update the UI to show an error message
      }
    }


