function submit_form(items, next_ref, current_task, experiment_id) {
      var done_mandatory = true;
      var form_value_dict = {};
      
      for (var item of items) {
            var fieldName = item.field;
            var element_value = "";
            var selectedRadio = document.querySelector('input[name="' + fieldName + '"]:checked');
            
            if (selectedRadio) {
                element_value = selectedRadio.value;
            } else {
                var element = document.getElementById(fieldName);
                if (element) {
                    element_value = element.value;
                }
            }

            form_value_dict[fieldName] = element_value;

            if (item.mandatory && (!element_value || element_value.trim() === "")) {
                done_mandatory = false;
            }
        }

      if (done_mandatory) {
          $.ajax({
            type: "POST",
            url: window.FLASK_URLS.task_questionnaire_submit,
            contentType: "application/json;charset=UTF-8",
            data: JSON.stringify({
                form_results: form_value_dict,
                nTask: current_task,
                expID: experiment_id
            }),

            success: function(response) {
              if (response.attention_limit || response.attention_limit === undefined) {
                    if (response.attention_reload){
                        if(response.attention_passed){
                            window.location.href = next_ref;
                        } else {
                            window.location.href = window.location.href;
                        }
                    } else {
                        window.location.href = next_ref;
                    }
              } else {
                  window.location.href = window.FLASK_URLS.stop_experiment;
              }
            },
            error: function(error) {
              console.log("Error:", error);
            }
          });
      } else {
        alert("Please select a value for all mandatory fields!");
      }
   }