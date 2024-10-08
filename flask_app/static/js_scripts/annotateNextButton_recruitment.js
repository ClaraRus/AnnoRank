    function getSelectedValuesScore(scoreBar, bar_name){
        checkValue = scoreBar.querySelector('input[name=' + bar_name + ']:checked');
        if (checkValue!==null){
            var selected_value = checkValue.value //scoreBar.querySelector('input[name='+bar_name +']:checked').value;
        return selected_value
        }else{
            return null
        }
    }

    function collectDataAnnotateRecruitment() {
      // Get all checkboxes with the name "item"
      var docWorkScore = getSelectedValuesScore(document.getElementById("score-bar-id_1"), "work_score");
      var docEduScore = getSelectedValuesScore(document.getElementById("score-bar-id_2"), "edu_score");
      var docSkillScore = getSelectedValuesScore(document.getElementById("score-bar-id_3"), "skills_score");
      var docOverallScore = getSelectedValuesScore(document.getElementById("score-bar-id_4"), "overall_score");

      var element = document.getElementById('doc_row');
      var docId = element.getAttribute('name');
      var element = document.getElementById('query_info');
      var queryId = element.getAttribute('qid');

      current_url = window.location.href;
      const expId = current_url.split('/')[4]
      const currentTask = parseInt(current_url.split('/')[6], 10)

      fetch('/api/'+expId+'/get_next_task/')
        .then(response => response.json())
        .then(data => {
            // Handle the data in your JavaScript code
            const nextTask = data.next_task;

            if (docWorkScore !== null && docEduScore !== null && docSkillScore !== null && docOverallScore !== null) {
              //Use jQuery AJAX to send data to the Flask app
                 $.ajax({
                type: "POST",
                url: "/store_data_annotate",
                contentType: "application/json;charset=UTF-8",
                data: JSON.stringify({

                score: [
                    ("work_score", docWorkScore),
                    ("edu_score", docEduScore),
                    ("skill_score", docSkillScore),
                    ("overall_score", docOverallScore)
                ],
                docId: docId,
                queryId: queryId,
                nTask: currentTask
                }),

        success: function(response) {
          if (nextTask == 'stop_experiment') {
            window.location.href = "/stop_experiment";
        } if (nextTask == 'form') {
            window.location.href ="/form"
            }
        else {
            // Redirect to the default link for other cases
            if (nextTask != '')
                {window.location.href = "/start_annotate/" + expId + "/index_annotate/" + nextTask ;}
        }
        },
        error: function(error) {
          console.log("Error:", error);
        }
      });
              } else {
                alert("Please select select a value for all score bars.");
             }
        })
        .catch(error => console.error('Error:', error));
    }
